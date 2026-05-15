# core/throttles.py
from rest_framework.throttling import BaseThrottle
from django.core.cache import cache
from django.conf import settings

from core.middleware.tracking import get_client_ip, record_throttle_violation


class AnonPostThrottle(BaseThrottle):
    """
    Limits anonymous POST requests per IP.
    Example: 20 posts per 30 minutes per ip,, controls contact, subscribe
    """

    RATE = 20
    WINDOW = 60 * 30  

    def allow_request(self, request, view):
        if request.user and request.user.is_authenticated:
            return True

        if request.method != "POST":
            return True

        ip = get_client_ip(request)
        if not ip:
            return True

        key = f"anon_post:{ip}"
        count = cache.get(key, 0)

        if count >= self.RATE:
            # record violation may ban
            record_throttle_violation(ip)
            return False

        cache.set(key, count + 1, self.WINDOW)
        return True