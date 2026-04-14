import logging

from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache

from config.models import BlockedIP

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str:
    """
    Return the real client IP, respecting X-Forwarded-For in production.
    In DEBUG mode, fall back to REMOTE_ADDR directly to avoid spoofing in dev.
    """
    if not settings.DEBUG:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


# ---------------------------------------------------------------------------
# IP block middleware
# ---------------------------------------------------------------------------

class IPBlockMiddleware:
    """
    Rejects requests from IPs listed in the BlockedIP table.
    Uses a short cache (60 s) to avoid a DB hit on every request.
    Place this BEFORE all other middleware so blocked traffic dies early.
    """

    CACHE_PREFIX = "blocked_ip:"
    CACHE_TTL    = 60  # seconds

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