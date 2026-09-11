from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AuthenticationTests(APITestCase):

    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.me_url = reverse("current_user")

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123!",
            "password_confirm": "TestPassword123!",
        }

    def test_user_registration(self):
        response = self.client.post(
            self.register_url,
            self.user_data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            User.objects.filter(
                username="testuser"
            ).exists()
        )

    def test_registration_password_mismatch(self):
        data = self.user_data.copy()

        data["password_confirm"] = "WrongPassword123!"

        response = self.client.post(
            self.register_url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_login_returns_tokens(self):
        User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!",
        )

        response = self.client.post(
            self.login_url,
            {
                "username": "testuser",
                "password": "TestPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

    def test_me_requires_authentication(self):
        response = self.client.get(
            self.me_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_me_returns_current_user(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!",
        )

        self.client.force_authenticate(
            user=user
        )

        response = self.client.get(
            self.me_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["username"],
            "testuser",
        )

        self.assertEqual(
            response.data["email"],
            "test@example.com",
        )