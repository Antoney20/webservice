from core.middleware.tracking import record_throttle_violation, get_client_ip
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class _ViolationMixin:
    def allow_request(self, request, view):
        self.request = request
        return super().allow_request(request, view)

    def throttle_failure(self):
        ip = get_client_ip(self.request)
        record_throttle_violation(ip)
        return super().throttle_failure()


class AnonBurstThrottle(_ViolationMixin, AnonRateThrottle):
    scope = "anon_burst"

class AnonSustainedThrottle(_ViolationMixin, AnonRateThrottle):
    scope = "anon_sustained"

class AuthBurstThrottle(_ViolationMixin, UserRateThrottle):
    scope = "auth_burst"

class AuthSustainedThrottle(_ViolationMixin, UserRateThrottle):
    scope = "auth_sustained"

class SensitiveAnonThrottle(_ViolationMixin, AnonRateThrottle):
    scope = "sensitive_anon"