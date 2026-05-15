from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def make_user(email="tester@cema.africa", password="TestPass99!", **kwargs):
    return User.objects.create_user(email=email, password=password, **kwargs)


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh), str(refresh.access_token)


def auth_client(user):
    _, access = get_tokens(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


class RefreshViewTests(TestCase):

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse("auth-refresh")
        self.user = make_user()

    def tearDown(self):
        cache.clear()

    def test_valid_refresh_returns_200(self):
        refresh_token, _ = get_tokens(self.user)
        res = self.client.post(self.url, {"refresh": refresh_token}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_valid_refresh_returns_new_token_pair(self):
        refresh_token, _ = get_tokens(self.user)
        res = self.client.post(self.url, {"refresh": refresh_token}, format="json")
        self.assertIn("access",  res.data)
        self.assertIn("refresh", res.data)

    def test_new_access_token_differs_from_old(self):
        refresh_token, old_access = get_tokens(self.user)
        res = self.client.post(self.url, {"refresh": refresh_token}, format="json")
        self.assertNotEqual(res.data["access"], old_access)

    def test_missing_refresh_field_returns_400(self):
        res = self.client.post(self.url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blank_refresh_field_returns_400(self):
        res = self.client.post(self.url, {"refresh": ""}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_malformed_token_returns_401(self):
        res = self.client.post(self.url, {"refresh": "not.a.real.token"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blacklisted_token_returns_401(self):
        refresh_token, _ = get_tokens(self.user)
        RefreshToken(refresh_token).blacklist()
        res = self.client.post(self.url, {"refresh": refresh_token}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blacklisted_token_error_mentions_expired(self):
        refresh_token, _ = get_tokens(self.user)
        RefreshToken(refresh_token).blacklist()
        res = self.client.post(self.url, {"refresh": refresh_token}, format="json")
        self.assertIn("expired", res.data["detail"].lower())

    def test_get_returns_405(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_returns_405(self):
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)



class LogoutViewTests(TestCase):

    def setUp(self):
        cache.clear()
        self.anon = APIClient()
        self.url         = reverse("auth-logout")
        self.refresh_url = reverse("auth-refresh")
        self.user = make_user()

    def tearDown(self):
        cache.clear()

    def _client_with_tokens(self):
        refresh_token, access_token = get_tokens(self.user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        return client, refresh_token

    def test_logout_returns_200(self):
        client, refresh_token = self._client_with_tokens()
        res = client.post(self.url, {"refresh": refresh_token}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_logout_response_has_detail(self):
        client, refresh_token = self._client_with_tokens()
        res = client.post(self.url, {"refresh": refresh_token}, format="json")
        self.assertIn("detail", res.data)

    def test_logout_blacklists_the_refresh_token(self):
        client, refresh_token = self._client_with_tokens()
        client.post(self.url, {"refresh": refresh_token}, format="json")

        res = self.anon.post(self.refresh_url, {"refresh": refresh_token}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_body_still_returns_200(self):
        client, _ = self._client_with_tokens()
        res = client.post(self.url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_logout_with_already_blacklisted_token_does_not_error(self):
        client, refresh_token = self._client_with_tokens()
        client.post(self.url, {"refresh": refresh_token}, format="json")
        # second call — same token, should still be 200
        res = client.post(self.url, {"refresh": refresh_token}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_logout_requires_authentication(self):
        res = self.anon.post(self.url, {"refresh": "token"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_405(self):
        client, _ = self._client_with_tokens()
        self.assertEqual(client.get(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_returns_405(self):
        client, _ = self._client_with_tokens()
        self.assertEqual(client.put(self.url, {}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

