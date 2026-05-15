from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


def make_user(email="tester@cema.africa", password="TestPass99!", **kwargs):
    return User.objects.create_user(email=email, password=password, **kwargs)


class LoginViewTests(TestCase):

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse("auth-login")
        self.user = make_user(name="Test User")

    def tearDown(self):
        cache.clear()

    def test_valid_credentials_return_200(self):
        res = self.client.post(self.url, {
            "email": "tester@cema.africa",
            "password": "TestPass99!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_response_contains_token_pair(self):
        res = self.client.post(self.url, {
            "email": "tester@cema.africa",
            "password": "TestPass99!",
        }, format="json")
        self.assertIn("access",  res.data)
        self.assertIn("refresh", res.data)

    def test_response_contains_user_fields(self):
        res = self.client.post(self.url, {
            "email": "tester@cema.africa",
            "password": "TestPass99!",
        }, format="json")
        user = res.data["user"]
        self.assertEqual(user["email"], "tester@cema.africa")
        self.assertEqual(user["name"],  "Test User")
        self.assertIn("id",   user)
        self.assertIn("role", user)

    def test_login_updates_last_login_timestamp(self):
        self.assertIsNone(self.user.last_login)
        self.client.post(self.url, {
            "email": "tester@cema.africa",
            "password": "TestPass99!",
        }, format="json")
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)

    def test_email_is_case_insensitive(self):
        res = self.client.post(self.url, {
            "email": "TESTER@CEMA.AFRICA",
            "password": "TestPass99!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_email_leading_trailing_whitespace_stripped(self):
        res = self.client.post(self.url, {
            "email": "  tester@cema.africa  ",
            "password": "TestPass99!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_wrong_password_returns_401(self):
        res = self.client.post(self.url, {
            "email": "tester@cema.africa",
            "password": "WrongPass!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_email_returns_401(self):
        res = self.client.post(self.url, {
            "email": "ghost@cema.africa",
            "password": "TestPass99!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_error_message_is_vague_on_wrong_password(self):
        """Must not reveal whether the email exists."""
        res = self.client.post(self.url, {
            "email": "tester@cema.africa",
            "password": "wrong",
        }, format="json")
        self.assertEqual(res.data["detail"], "Invalid email or password.")

    def test_error_message_is_vague_on_unknown_email(self):
        res = self.client.post(self.url, {
            "email": "ghost@cema.africa",
            "password": "wrong",
        }, format="json")
        self.assertEqual(res.data["detail"], "Invalid email or password.")


    def test_missing_email_returns_400(self):
        res = self.client.post(self.url, {"password": "TestPass99!"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_returns_400(self):
        res = self.client.post(self.url, {"email": "tester@cema.africa"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_body_returns_400(self):
        res = self.client.post(self.url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blank_email_string_returns_400(self):
        res = self.client.post(self.url, {"email": "   ", "password": "TestPass99!"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    def test_inactive_user_returns_403(self):
        self.user.is_active = False
        self.user.save()
        res = self.client.post(self.url, {
            "email": "tester@cema.africa",
            "password": "TestPass99!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_user_message_mentions_suspended(self):
        self.user.is_active = False
        self.user.save()
        res = self.client.post(self.url, {
            "email": "tester@cema.africa",
            "password": "TestPass99!",
        }, format="json")
        self.assertIn("suspended", res.data["detail"].lower())

    def test_get_returns_405(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_returns_405(self):
        self.assertEqual(self.client.put(self.url, {}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_returns_405(self):
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)