from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from sites.models import Site


User = get_user_model()


class SiteSecurityTests(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            username="user_a",
            email="usera@example.com",
            password="TestPassword123!",
        )

        self.user_b = User.objects.create_user(
            username="user_b",
            email="userb@example.com",
            password="TestPassword123!",
        )

        self.site_a = Site.objects.create(
            user=self.user_a,
            name="User A Site",
            location="Location A",
            description="Site belonging to User A",
        )

        self.site_b = Site.objects.create(
            user=self.user_b,
            name="User B Site",
            location="Location B",
            description="Site belonging to User B",
        )

        self.list_url = reverse("site-list-create")

    def test_unauthenticated_user_cannot_access_sites(self):
        response = self.client.get(
            self.list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_user_only_sees_own_sites(self):
        self.client.force_authenticate(
            user=self.user_a
        )

        response = self.client.get(
            self.list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = [
            site["id"]
            for site in response.data
        ]

        self.assertIn(
            self.site_a.id,
            returned_ids,
        )

        self.assertNotIn(
            self.site_b.id,
            returned_ids,
        )

    def test_user_cannot_retrieve_another_users_site(self):
        self.client.force_authenticate(
            user=self.user_a
        )

        url = reverse(
            "site-detail",
            kwargs={
                "pk": self.site_b.id
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_cannot_update_another_users_site(self):
        self.client.force_authenticate(
            user=self.user_a
        )

        url = reverse(
            "site-detail",
            kwargs={
                "pk": self.site_b.id
            },
        )

        response = self.client.patch(
            url,
            {
                "name": "HACKED SITE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.site_b.refresh_from_db()

        self.assertEqual(
            self.site_b.name,
            "User B Site",
        )

    def test_user_cannot_delete_another_users_site(self):
        self.client.force_authenticate(
            user=self.user_a
        )

        url = reverse(
            "site-detail",
            kwargs={
                "pk": self.site_b.id
            },
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            Site.objects.filter(
                id=self.site_b.id
            ).exists()
        )

    def test_user_can_create_own_site(self):
        self.client.force_authenticate(
            user=self.user_a
        )

        response = self.client.post(
            self.list_url,
            {
                "name": "New User A Site",
                "location": "Location C",
                "description": "New construction site",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        created_site = Site.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            created_site.user,
            self.user_a,
        )

    def test_site_code_is_generated(self):
        self.client.force_authenticate(
            user=self.user_a
        )

        response = self.client.post(
            self.list_url,
            {
                "name": "Another User A Site",
                "location": "Location D",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            response.data["code"].startswith("S")
        )