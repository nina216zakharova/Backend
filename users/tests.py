from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from users.models import GoogleProfile
from users.services import generate_password_reset_token

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


class PasswordResetRequestTests(TestCase):
    def setUp(self):
        self.endpoint = "/api/users/password-reset/"
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset.user@example.com",
            password="originalPassword123",
        )

    def test_request_reset_valid_active_user(self):
        response = self.client.post(
            self.endpoint,
            {"email": "reset.user@example.com"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

        # Verify email was dispatched to outbox
        self.assertEqual(len(mail.outbox), 1)
        email_msg = mail.outbox[0]
        self.assertEqual(email_msg.to, ["reset.user@example.com"])
        self.assertIn("بازیابی رمز عبور", email_msg.subject)
        self.assertIn("uid=", email_msg.body)
        self.assertIn("token=", email_msg.body)

    def test_request_reset_case_insensitive_email(self):
        response = self.client.post(
            self.endpoint,
            {"email": "RESET.USER@EXAMPLE.COM"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["reset.user@example.com"])

    def test_request_reset_nonexistent_email_does_not_leak_enumeration(self):
        response = self.client.post(
            self.endpoint,
            {"email": "nonexistent@example.com"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(len(mail.outbox), 0)

    def test_request_reset_inactive_user(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            self.endpoint,
            {"email": "reset.user@example.com"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_request_reset_invalid_email_format(self):
        response = self.client.post(
            self.endpoint,
            {"email": "not-a-valid-email"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json())

    def test_request_reset_custom_redirect_url(self):
        custom_url = "https://myapp.com/auth/new-password"
        response = self.client.post(
            self.endpoint,
            {
                "email": "reset.user@example.com",
                "redirect_url": custom_url,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(custom_url, mail.outbox[0].body)


class PasswordResetValidateTests(TestCase):
    def setUp(self):
        self.endpoint = "/api/users/password-reset/validate/"
        self.user = User.objects.create_user(
            username="validatetest",
            email="validate@example.com",
            password="securePassword123",
        )
        self.uid, self.token = generate_password_reset_token(self.user)

    def test_validate_token_success_post(self):
        response = self.client.post(
            self.endpoint,
            {"uid": self.uid, "token": self.token},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["username"], "validatetest")

    def test_validate_token_success_get(self):
        response = self.client.get(
            f"{self.endpoint}?uid={self.uid}&token={self.token}",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["valid"])

    def test_validate_token_invalid_token(self):
        response = self.client.post(
            self.endpoint,
            {"uid": self.uid, "token": "invalid-tampered-token"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["valid"])

    def test_validate_token_invalid_uid(self):
        response = self.client.post(
            self.endpoint,
            {"uid": "invalid-uid-b64", "token": self.token},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["valid"])

    def test_validate_token_inactive_user(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            self.endpoint,
            {"uid": self.uid, "token": self.token},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["valid"])


class PasswordResetConfirmTests(TestCase):
    def setUp(self):
        self.endpoint = "/api/users/password-reset/confirm/"
        self.user = User.objects.create_user(
            username="confirmuser",
            email="confirm@example.com",
            password="initialPassword123",
        )
        self.token_initial = Token.objects.create(user=self.user)
        self.uid, self.reset_token = generate_password_reset_token(self.user)

    def test_confirm_password_reset_success(self):
        payload = {
            "uid": self.uid,
            "token": self.reset_token,
            "new_password": "brandNewPassword999",
            "confirm_password": "brandNewPassword999",
        }
        response = self.client.post(
            self.endpoint,
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("token", data)

        # Check DB that password was updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("brandNewPassword999"))
        self.assertFalse(self.user.check_password("initialPassword123"))

        # Verify old token was revoked/replaced
        self.assertNotEqual(data["token"], self.token_initial.key)

        # Token cannot be reused a second time (one-time usage!)
        second_attempt = self.client.post(
            self.endpoint,
            payload,
            content_type="application/json",
        )
        self.assertEqual(second_attempt.status_code, 400)

    def test_confirm_password_reset_mismatched_passwords(self):
        payload = {
            "uid": self.uid,
            "token": self.reset_token,
            "new_password": "passwordA123",
            "confirm_password": "passwordB123",
        }
        response = self.client.post(
            self.endpoint,
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("confirm_password", response.json())

    def test_confirm_password_reset_short_password(self):
        payload = {
            "uid": self.uid,
            "token": self.reset_token,
            "new_password": "short",
            "confirm_password": "short",
        }
        response = self.client.post(
            self.endpoint,
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_confirm_password_reset_invalid_or_expired_token(self):
        payload = {
            "uid": self.uid,
            "token": "expired-or-tampered-token",
            "new_password": "validNewPassword123",
            "confirm_password": "validNewPassword123",
        }
        response = self.client.post(
            self.endpoint,
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.endpoint = "/api/users/password-change/"
        self.user = User.objects.create_user(
            username="changepassworduser",
            email="change@example.com",
            password="currentPassword123",
        )
        self.token = Token.objects.create(user=self.user)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}

    def test_change_password_authenticated_success(self):
        payload = {
            "old_password": "currentPassword123",
            "new_password": "updatedPassword456",
            "confirm_password": "updatedPassword456",
        }
        response = self.client.post(
            self.endpoint,
            payload,
            content_type="application/json",
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("updatedPassword456"))

    def test_change_password_wrong_old_password(self):
        payload = {
            "old_password": "wrongPassword123",
            "new_password": "updatedPassword456",
            "confirm_password": "updatedPassword456",
        }
        response = self.client.post(
            self.endpoint,
            payload,
            content_type="application/json",
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("old_password", response.json())

    def test_change_password_mismatched_confirmation(self):
        payload = {
            "old_password": "currentPassword123",
            "new_password": "updatedPassword456",
            "confirm_password": "differentPassword789",
        }
        response = self.client.post(
            self.endpoint,
            payload,
            content_type="application/json",
            **self.auth_headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("confirm_password", response.json())

    def test_change_password_unauthenticated_fails(self):
        payload = {
            "old_password": "currentPassword123",
            "new_password": "updatedPassword456",
            "confirm_password": "updatedPassword456",
        }
        response = self.client.post(
            self.endpoint,
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

