import logging

from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache

from config.models import BlockedIP

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str:
    if not settings.DEBUG:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class IPBlockMiddleware:
    """
    Rejects requests from IPs in the BlockedIP table.
    Throttle violations auto-create a BlockedIP record after VIOLATION_THRESHOLD breaches.
    """

    CACHE_PREFIX       = "blocked_ip:"
    CACHE_TTL          = 60

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = get_client_ip(request)
        if ip and self._is_blocked(ip):
            logger.warning("Blocked IP attempted access: %s %s", ip, request.path)
            return JsonResponse({"detail": "Access denied."}, status=403)
        return self.get_response(request)

    def _is_blocked(self, ip: str) -> bool:
        key = f"{self.CACHE_PREFIX}{ip}"
        cached = cache.get(key)
        if cached is not None:
            return cached
        blocked = BlockedIP.objects.filter(ip_address=ip).exists()
        cache.set(key, blocked, self.CACHE_TTL)
        return blocked


# ---------------------------------------------------------------------------
# Called by throttles on violation — no separate ban cache key needed
# ---------------------------------------------------------------------------

VIOLATION_KEY       = "throttle_violations:{ip}"
VIOLATION_THRESHOLD = 5
VIOLATION_WINDOW    = 60 * 10  # 10 min


def record_throttle_violation(ip: str) -> None:
    """
    Increment violation counter. On hitting the threshold, write a BlockedIP
    row and poison the middleware cache so the ban takes effect immediately.
    """
    key        = VIOLATION_KEY.format(ip=ip)
    violations = (cache.get(key) or 0) + 1
    cache.set(key, violations, VIOLATION_WINDOW)

    if violations >= VIOLATION_THRESHOLD:
        _, created = BlockedIP.objects.get_or_create(
            ip_address=ip,
            defaults={"reason": "Auto-banned: repeated throttle violations"},
        )
        if created:
            # Push ban into cache immediately — don't wait for next 60 s cycle
            cache.set(f"{IPBlockMiddleware.CACHE_PREFIX}{ip}", True, IPBlockMiddleware.CACHE_TTL)
            logger.warning("Auto-banned IP after %d throttle violations: %s", violations, ip)