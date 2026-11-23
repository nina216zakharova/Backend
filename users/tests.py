from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from users.models import GoogleProfile

User = get_user_model()


class UsersAPITest(TestCase):
    def test_users_api_returns_success(self):
        response = self.client.get("/api/users/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "message": "API is working!",
                "status": "success",
            },
        )


class GoogleAuthTests(TestCase):
    def setUp(self):
        self.endpoint = "/api/users/google/"

    @patch("users.services.verify_id_token")
    def test_signup_new_user_via_id_token(self, mock_verify):
        mock_verify.return_value = {
            "email": "alex.doe@example.com",
            "email_verified": True,
            "name": "Alex Doe",
            "sub": "google-uid-1001",
            "picture": "https://example.com/avatar.jpg",
        }

        response = self.client.post(self.endpoint, {"id_token": "valid_mock_token"}, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        self.assertTrue(data["is_new_user"])
        self.assertEqual(data["user"]["email"], "alex.doe@example.com")
        self.assertEqual(data["user"]["username"], "alex_doe")

        user = User.objects.get(email="alex.doe@example.com")
        self.assertFalse(user.has_usable_password())

        profile = GoogleProfile.objects.get(user=user)
        self.assertEqual(profile.google_id, "google-uid-1001")
        self.assertEqual(profile.picture, "https://example.com/avatar.jpg")

    @patch("users.services.verify_id_token")
    def test_login_existing_user_via_id_token(self, mock_verify):
        user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="securePassword123",
        )
        existing_token = Token.objects.create(user=user)

        mock_verify.return_value = {
            "email": "existing@example.com",
            "email_verified": True,
            "sub": "google-uid-1002",
        }

        response = self.client.post(self.endpoint, {"id_token": "valid_mock_token"}, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_new_user"])
        self.assertEqual(data["token"], existing_token.key)
        self.assertEqual(data["user"]["email"], "existing@example.com")
        self.assertEqual(data["user"]["username"], "existinguser")

    @patch("users.services.verify_access_token")
    def test_auth_via_access_token(self, mock_verify):
        mock_verify.return_value = {
            "email": "access.user@example.com",
            "email_verified": True,
            "name": "Access User",
            "sub": "google-uid-1003",
        }

        response = self.client.post(
            self.endpoint,
            {"access_token": "mock_access_token"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_new_user"])
        self.assertEqual(data["user"]["email"], "access.user@example.com")

    @patch("users.services.exchange_auth_code")
    def test_auth_via_authorization_code(self, mock_exchange):
        mock_exchange.return_value = {
            "email": "code.user@example.com",
            "email_verified": True,
            "name": "Code User",
            "sub": "google-uid-1004",
        }

        response = self.client.post(
            self.endpoint,
            {"code": "auth_code_sample", "redirect_uri": "http://localhost:5173/auth/callback"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_new_user"])
        self.assertEqual(data["user"]["email"], "code.user@example.com")

    def test_missing_credentials_fails(self):
        response = self.client.post(self.endpoint, {}, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    @patch("users.services.verify_id_token")
    def test_unverified_email_fails(self, mock_verify):
        mock_verify.return_value = {
            "email": "unverified@example.com",
            "email_verified": False,
            "sub": "google-uid-1005",
        }

        response = self.client.post(self.endpoint, {"id_token": "token"}, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    @patch("users.services.verify_id_token")
    def test_invalid_token_fails(self, mock_verify):
        mock_verify.side_effect = AuthenticationFailed("Invalid Google ID token.")

        response = self.client.post(self.endpoint, {"id_token": "bad_token"}, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    @patch("users.services.verify_id_token")
    def test_inactive_user_fails(self, mock_verify):
        User.objects.create_user(
            username="disableduser",
            email="disabled@example.com",
            password="password123",
            is_active=False,
        )

        mock_verify.return_value = {
            "email": "disabled@example.com",
            "email_verified": True,
            "sub": "google-uid-1006",
        }

        response = self.client.post(self.endpoint, {"id_token": "valid_token"}, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_google_login_redirect_url_generation(self):
        response = self.client.get("/api/users/google/login/?format=json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("auth_url", response.json())
        self.assertIn("accounts.google.com", response.json()["auth_url"])

    @patch("users.views.authenticate_google")
    def test_google_callback_success(self, mock_auth):
        user = User.objects.create_user(
            username="callbackuser",
            email="callback@example.com",
            password="password123",
        )
        token = Token.objects.create(user=user)
        mock_auth.return_value = (user, token, False)

        response = self.client.get("/api/users/google/callback/?code=mock_code")
        self.assertEqual(response.status_code, 302)
        self.assertIn(token.key, response.url)

    def test_google_callback_error(self):
        response = self.client.get("/api/users/google/callback/?error=access_denied")
        self.assertEqual(response.status_code, 302)
        self.assertIn("error=access_denied", response.url)
