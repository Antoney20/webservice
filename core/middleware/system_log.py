import logging
import time
import traceback

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

DEFAULT_SKIP = ("/static/", "/media/", "/favicon.ico", "/admin/jsi18n/")
DEFAULT_SLOW_MS = 4000  # 4 seconds


def client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


class SystemLogMiddleware:
    """
    Writes to SystemLog:
      ERROR   - 5xx responses and unhandled exceptions (with stack trace)
      WARNING - 4xx responses and slow requests (>= 4 s)
      INFO    - everything else, only if SYSTEM_LOG_MIN_STATUS <= 200
    created_at is set automatically (auto_now_add); the request start time
    is kept in metadata["started_at"].
    Never raises: a logging failure must not break the request.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.min_status = getattr(settings, "SYSTEM_LOG_MIN_STATUS", 400)
        self.slow_ms = getattr(settings, "SYSTEM_LOG_SLOW_MS", DEFAULT_SLOW_MS)
        self.skip = tuple(getattr(settings, "SYSTEM_LOG_SKIP_PREFIXES", DEFAULT_SKIP))

    def __call__(self, request):
        if request.path.startswith(self.skip):
            return self.get_response(request)

        started_at = timezone.now()
        start = time.monotonic()
        response = self.get_response(request)   # unhandled errors come back here as a 500
        duration = int((time.monotonic() - start) * 1000)

        try:
            self._record(request, response.status_code, duration, started_at)
        except Exception:
            logger.exception("SystemLogMiddleware failed to record request")
        return response

    def process_exception(self, request, exception):
        request._syslog_exc = exception
        request._syslog_stack = "".join(
            traceback.format_exception(type(exception), exception, exception.__traceback__)
        )
        return None  # let Django / DRF handle it as usual

    # ------------------------------------------------------------------
    def _record(self, request, status, duration, started_at):
        exc = getattr(request, "_syslog_exc", None)
        slow = duration >= self.slow_ms

        if exc is not None or status >= 500:
            level = "ERROR"
        elif status >= 400 or slow:
            level = "WARNING"
        else:
            level = "INFO"

        if not (exc is not None or slow or status >= self.min_status):
            return

        from config.models import SystemLog   # lazy import

        user = getattr(request, "user", None)
        user_id = str(user.pk) if user is not None and getattr(user, "is_authenticated", False) else None

        match = getattr(request, "resolver_match", None)
        message = f"{request.method} {request.path} -> {status} ({duration} ms)"
        if exc is not None:
            message = f"{type(exc).__name__}: {exc} | {message}"

        SystemLog.objects.create(
            level=level,
            message=message[:5000],
            component=(match.view_name if match and match.view_name else "unresolved")[:255],
            route=request.get_full_path()[:500],
            method=request.method,
            status_code=status,
            ip_address=client_ip(request),
            user_id=user_id,
            duration=duration,
            stack=getattr(request, "_syslog_stack", None),
            metadata={
                "slow": slow,
                "slow_threshold_ms": self.slow_ms,
                "started_at": started_at.isoformat(),
                "content_type": request.META.get("CONTENT_TYPE", ""),
                "user_agent": request.META.get("HTTP_USER_AGENT", "")[:500],
            },
        )