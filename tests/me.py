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




class MeViewTests(TestCase):

    def setUp(self):
        cache.clear()
        self.url = reverse("auth-me")
        self.user = make_user(name="Test User")

    def tearDown(self):
        cache.clear()

    def test_me_returns_200(self):
        res = auth_client(self.user).get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_me_returns_correct_email(self):
        res = auth_client(self.user).get(self.url)
        self.assertEqual(res.data["email"], "tester@cema.africa")

    def test_me_returns_correct_name(self):
        res = auth_client(self.user).get(self.url)
        self.assertEqual(res.data["name"], "Test User")

    def test_me_returns_is_active_true(self):
        res = auth_client(self.user).get(self.url)
        self.assertTrue(res.data["is_active"])

    def test_me_returns_id_and_role(self):
        res = auth_client(self.user).get(self.url)
        self.assertIn("id",   res.data)
        self.assertIn("role", res.data)

    def test_me_unauthenticated_returns_401(self):
        res = APIClient().get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_fake_token_returns_401(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer fake.jwt.payload")
        res = client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_expired_access_token_returns_401(self):
        """Refresh token used as access token — wrong type, must be rejected."""
        refresh_token, _ = get_tokens(self.user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh_token}")
        res = client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_returns_405(self):
        self.assertEqual(auth_client(self.user).post(self.url, {}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_returns_405(self):
        self.assertEqual(auth_client(self.user).delete(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)