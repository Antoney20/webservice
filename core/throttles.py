from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


# ---------------------------------------------------------------------------
# Anonymous throttles  (applied to public / unauthenticated endpoints)
# ---------------------------------------------------------------------------

class AnonBurstThrottle(AnonRateThrottle):
    """Short burst limit — prevents rapid-fire abuse."""
    scope = "anon_burst"       # maps to THROTTLE_RATES["anon_burst"]


class AnonSustainedThrottle(AnonRateThrottle):
    """Sustained hourly cap for anonymous users."""
    scope = "anon_sustained"


# ---------------------------------------------------------------------------
# Authenticated throttles
# ---------------------------------------------------------------------------

class AuthBurstThrottle(UserRateThrottle):
    scope = "auth_burst"


class AuthSustainedThrottle(UserRateThrottle):
    scope = "auth_sustained"


# ---------------------------------------------------------------------------
# Strict throttle — for sensitive write endpoints (subscribe, contact)
# ---------------------------------------------------------------------------

class SensitiveAnonThrottle(AnonRateThrottle):
    """
    Very tight limit for anonymous write endpoints.
    Blocks after a small number of submissions per hour.
    """
    scope = "sensitive_anon"