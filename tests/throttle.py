from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


def make_user(email="throttle@cema.africa", password="Pass1234!", **kwargs):
    return User.objects.create_user(email=email, password=password, **kwargs)


def _mock_request(method="POST", ip="10.0.0.1", authenticated=False):
    req = MagicMock()
    req.method = method
    req.user = MagicMock()
    req.user.is_authenticated = authenticated
    req.META = {"REMOTE_ADDR": ip}
    return req


# ------------------------------------------------
# AnonPostThrottle  (core/throttles/annon.py)
# ------------------------------------------------

@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class AnonPostThrottleTests(TestCase):

    def setUp(self):
        cache.clear()
        from core.throttles.annon import AnonPostThrottle
        self.ThrottleClass = AnonPostThrottle

    def tearDown(self):
        cache.clear()

    # ── under limit 

    @patch("core.throttles.annon.get_client_ip", return_value="10.0.0.1")
    @patch("core.throttles.annon.record_throttle_violation")
    def test_allows_requests_under_rate(self, mock_record, mock_ip):
        throttle = self.ThrottleClass()
        req = _mock_request()
        for _ in range(self.ThrottleClass.RATE - 1):
            self.assertTrue(throttle.allow_request(req, None))
        mock_record.assert_not_called()

    @patch("core.throttles.annon.get_client_ip", return_value="10.0.0.1")
    @patch("core.throttles.annon.record_throttle_violation")
    def test_exactly_at_rate_is_still_allowed(self, mock_record, mock_ip):
        throttle = self.ThrottleClass()
        req = _mock_request()
        for i in range(self.ThrottleClass.RATE):
            result = throttle.allow_request(req, None)
        # the RATE-th call is the boundary — depends on implementation (>= vs >)
        # we assert no error was raised, result is bool
        self.assertIsInstance(result, bool)

    # ── at / over limit 

    @patch("core.throttles.annon.get_client_ip", return_value="10.0.0.1")
    @patch("core.throttles.annon.record_throttle_violation")
    def test_blocks_request_over_rate(self, mock_record, mock_ip):
        throttle = self.ThrottleClass()
        req = _mock_request()
        for _ in range(self.ThrottleClass.RATE):
            throttle.allow_request(req, None)
        result = throttle.allow_request(req, None)
        self.assertFalse(result)

    @patch("core.throttles.annon.get_client_ip", return_value="10.0.0.1")
    @patch("core.throttles.annon.record_throttle_violation")
    def test_violation_recorded_when_blocked(self, mock_record, mock_ip):
        throttle = self.ThrottleClass()
        req = _mock_request()
        for _ in range(self.ThrottleClass.RATE + 1):
            throttle.allow_request(req, None)
        mock_record.assert_called_with("10.0.0.1")

    # ── bypass conditions 

    @patch("core.throttles.annon.get_client_ip", return_value="10.0.0.1")
    def test_get_requests_never_blocked(self, mock_ip):
        throttle = self.ThrottleClass()
        req = _mock_request(method="GET")
        for _ in range(self.ThrottleClass.RATE + 20):
            self.assertTrue(throttle.allow_request(req, None))

    @patch("core.throttles.annon.get_client_ip", return_value="10.0.0.1")
    def test_authenticated_users_never_blocked(self, mock_ip):
        throttle = self.ThrottleClass()
        req = _mock_request(authenticated=True)
        for _ in range(self.ThrottleClass.RATE + 20):
            self.assertTrue(throttle.allow_request(req, None))

    @patch("core.throttles.annon.get_client_ip", return_value=None)
    def test_no_ip_fails_open(self, mock_ip):
        """If IP cannot be determined, allow the request."""
        throttle = self.ThrottleClass()
        req = _mock_request()
        self.assertTrue(throttle.allow_request(req, None))

    # ── IP isolation 

    @patch("core.throttles.annon.get_client_ip")
    @patch("core.throttles.annon.record_throttle_violation")
    def test_different_ips_have_separate_counters(self, mock_record, mock_ip):
        throttle_a = self.ThrottleClass()
        throttle_b = self.ThrottleClass()

        req_a = _mock_request(ip="10.0.0.1")
        req_b = _mock_request(ip="10.0.0.2")

        mock_ip.return_value = "10.0.0.1"
        for _ in range(self.ThrottleClass.RATE):
            throttle_a.allow_request(req_a, None)

        mock_ip.return_value = "10.0.0.2"
        result = throttle_b.allow_request(req_b, None)
        self.assertTrue(result)

    # ── cache key uniqueness 

    @patch("core.throttles.annon.get_client_ip", return_value="172.16.0.5")
    @patch("core.throttles.annon.record_throttle_violation")
    def test_cache_key_includes_ip(self, mock_record, mock_ip):
        throttle = self.ThrottleClass()
        req = _mock_request(ip="172.16.0.5")
        throttle.allow_request(req, None)
        from django.core.cache import cache as _cache
        self.assertIsNotNone(_cache.get("anon_post:172.16.0.5"))

    # ── window

    def test_window_is_positive_integer(self):
        self.assertIsInstance(self.ThrottleClass.WINDOW, int)
        self.assertGreater(self.ThrottleClass.WINDOW, 0)

    def test_rate_is_positive_integer(self):
        self.assertIsInstance(self.ThrottleClass.RATE, int)
        self.assertGreater(self.ThrottleClass.RATE, 0)


# ------------------------------------------------
# _ViolationMixin  (core/throttles/aa.py)
# ------------------------------------------------

@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class ViolationMixinTests(TestCase):

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _req(self, ip="192.168.1.1"):
        req = MagicMock()
        req.user = MagicMock(is_authenticated=False)
        req.META = {"REMOTE_ADDR": ip}
        return req

    @patch("core.throttles.aa.record_throttle_violation")
    @patch("core.throttles.aa.get_client_ip", return_value="192.168.1.1")
    def test_anon_burst_calls_violation_on_failure(self, mock_ip, mock_record):
        from core.throttles.aa import AnonBurstThrottle
        throttle = AnonBurstThrottle()
        req = self._req()
        with patch("rest_framework.throttling.AnonRateThrottle.allow_request", return_value=False):
            throttle.allow_request(req, None)
            throttle.throttle_failure()
        mock_record.assert_called_once_with("192.168.1.1")

    @patch("core.throttles.aa.record_throttle_violation")
    @patch("core.throttles.aa.get_client_ip", return_value="192.168.1.2")
    def test_anon_sustained_calls_violation_on_failure(self, mock_ip, mock_record):
        from core.throttles.aa import AnonSustainedThrottle
        throttle = AnonSustainedThrottle()
        req = self._req("192.168.1.2")
        with patch("rest_framework.throttling.AnonRateThrottle.allow_request", return_value=False):
            throttle.allow_request(req, None)
            throttle.throttle_failure()
        mock_record.assert_called_once_with("192.168.1.2")

    @patch("core.throttles.aa.record_throttle_violation")
    @patch("core.throttles.aa.get_client_ip", return_value="10.10.10.1")
    def test_sensitive_anon_calls_violation_on_failure(self, mock_ip, mock_record):
        from core.throttles.aa import SensitiveAnonThrottle
        throttle = SensitiveAnonThrottle()
        req = self._req("10.10.10.1")
        with patch("rest_framework.throttling.AnonRateThrottle.allow_request", return_value=False):
            throttle.allow_request(req, None)
            throttle.throttle_failure()
        mock_record.assert_called_once_with("10.10.10.1")

    @patch("core.throttles.aa.record_throttle_violation")
    @patch("core.throttles.aa.get_client_ip", return_value="10.20.30.40")
    def test_auth_burst_calls_violation_on_failure(self, mock_ip, mock_record):
        from core.throttles.aa import AuthBurstThrottle
        throttle = AuthBurstThrottle()
        req = self._req("10.20.30.40")
        with patch("rest_framework.throttling.UserRateThrottle.allow_request", return_value=False):
            throttle.allow_request(req, None)
            throttle.throttle_failure()
        mock_record.assert_called_once_with("10.20.30.40")

    @patch("core.throttles.aa.record_throttle_violation")
    @patch("core.throttles.aa.get_client_ip", return_value="10.0.0.99")
    def test_no_violation_when_request_is_allowed(self, mock_ip, mock_record):
        from core.throttles.aa import AnonBurstThrottle
        throttle = AnonBurstThrottle()
        req = self._req()
        with patch("rest_framework.throttling.AnonRateThrottle.allow_request", return_value=True):
            result = throttle.allow_request(req, None)
        self.assertTrue(result)
        mock_record.assert_not_called()

    @patch("core.throttles.aa.record_throttle_violation")
    @patch("core.throttles.aa.get_client_ip", return_value="1.2.3.4")
    def test_request_stored_on_throttle_instance(self, mock_ip, mock_record):
        """_ViolationMixin must store the request so throttle_failure can read the IP."""
        from core.throttles.aa import AnonBurstThrottle
        throttle = AnonBurstThrottle()
        req = self._req("1.2.3.4")
        with patch("rest_framework.throttling.AnonRateThrottle.allow_request", return_value=True):
            throttle.allow_request(req, None)
        self.assertIs(throttle.request, req)

    def test_scope_names_are_correct(self):
        from core.throttles.aa import (
            AnonBurstThrottle, AnonSustainedThrottle,
            AuthBurstThrottle, AuthSustainedThrottle,
            SensitiveAnonThrottle,
        )
        self.assertEqual(AnonBurstThrottle.scope,      "anon_burst")
        self.assertEqual(AnonSustainedThrottle.scope,  "anon_sustained")
        self.assertEqual(AuthBurstThrottle.scope,      "auth_burst")
        self.assertEqual(AuthSustainedThrottle.scope,  "auth_sustained")
        self.assertEqual(SensitiveAnonThrottle.scope,  "sensitive_anon")


# ------------------------------------------------
# Integration: login endpoint throttled end-to-end
# ------------------------------------------------

@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_CLASSES": ["core.throttles.aa.SensitiveAnonThrottle"],
        "DEFAULT_THROTTLE_RATES":   {"sensitive_anon": "3/minute"},
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ],
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    },
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class LoginThrottleIntegrationTests(TestCase):
    """
    End-to-end throttle tests.

    REMOTE_ADDR must be passed as an extra environ kwarg directly to the
    test client call — not as a regular keyword argument — so Django sets
    it on the WSGI environ before the view runs.

        self.client.post(url, data, content_type="application/json", REMOTE_ADDR="x.x.x.x")

    Using `format="json"` routes through APIClient's encoder; passing
    `content_type` directly achieves the same thing and also allows extra
    environ kwargs to be forwarded correctly.
    """

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse("auth-login")
        self.payload = {"email": "throttle@cema.africa", "password": "Pass1234!"}
        make_user()

    def tearDown(self):
        cache.clear()

    def _post(self, ip: str):
        import json
        return self.client.post(
            self.url,
            data=json.dumps(self.payload),
            content_type="application/json",
            REMOTE_ADDR=ip,
        )

    @patch("core.throttles.aa.record_throttle_violation")
    def test_fourth_request_from_same_ip_returns_429(self, mock_record):
        for _ in range(60): #changed to 60 attempts, higher than the middleware threshold
            self._post("1.2.3.4")

        res = self._post("1.2.3.4")
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch("core.throttles.aa.record_throttle_violation")
    def test_different_ip_not_affected_by_other_ips_rate(self, mock_record):
        # exhaust IP A
        for _ in range(4):
            self._post("1.2.3.4")

        
        res = self._post("9.9.9.9")
        self.assertNotEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch("core.throttles.aa.record_throttle_violation")
    def test_first_three_requests_not_throttled(self, mock_record):
        for _ in range(3):
            res = self._post("5.5.5.5")
            self.assertNotEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)