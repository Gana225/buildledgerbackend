from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from mesthiri.models import Mesthiri, MesthiriAssignment, MesthiriEntry
from sites.models import Site

User = get_user_model()


class MesthiriTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="mesthiri_a", email="mesthiri_a@example.com", password="TestPassword123!")
        self.user_b = User.objects.create_user(username="mesthiri_b", email="mesthiri_b@example.com", password="TestPassword123!")
        self.site_a = Site.objects.create(user=self.user_a, name="User A Site")
        self.site_b = Site.objects.create(user=self.user_b, name="User B Site")
        self.mesthiri_a = Mesthiri.objects.create(user=self.user_a, name="Raju")
        self.mesthiri_b = Mesthiri.objects.create(user=self.user_b, name="Babu")
        MesthiriAssignment.objects.create(mesthiri=self.mesthiri_a, site=self.site_a, start_date=date(2026, 1, 1))
        MesthiriAssignment.objects.create(mesthiri=self.mesthiri_b, site=self.site_b, start_date=date(2026, 1, 1))
        self.client.force_authenticate(user=self.user_a)
        self.mesthiri_list_url = reverse("mesthiri-list-create")
        self.entry_list_url = reverse("mesthiri-site-entry-list-create", kwargs={"site_id": self.site_a.id})

    def test_user_can_create_mesthiri(self):
        response = self.client.post(self.mesthiri_list_url, {"name": "Kumar"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Mesthiri.objects.filter(user=self.user_a, name="Kumar").exists())

    def test_user_only_sees_own_mesthiri_and_site_filter(self):
        response = self.client.get(self.mesthiri_list_url, {"site": self.site_a.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [self.mesthiri_a.id])

    def test_assignment_closes_previous_open_assignment(self):
        site_c = Site.objects.create(user=self.user_a, name="Second Site")
        url = reverse("mesthiri-assignment-list-create", kwargs={"mesthiri_id": self.mesthiri_a.id})
        response = self.client.post(url, {"site": site_c.id, "start_date": "2026-09-10"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MesthiriAssignment.objects.get(mesthiri=self.mesthiri_a, site=self.site_a).end_date, date(2026, 9, 9))

    def test_entry_validation_and_remaining_amount(self):
        invalid = self.client.post(self.entry_list_url, {"mesthiri": self.mesthiri_a.id, "date": "2026-09-10", "wage": "100", "paid_amount": "120"}, format="json")
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(self.entry_list_url, {"mesthiri": self.mesthiri_a.id, "date": "2026-09-10", "wage": "1000", "paid_amount": "600"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["remaining_amount"], "400.00")

    def test_duplicate_daily_entry_is_rejected(self):
        MesthiriEntry.objects.create(mesthiri=self.mesthiri_a, site=self.site_a, date="2026-09-10", wage=Decimal("1000.00"), paid_amount=Decimal("500.00"))
        response = self.client.post(self.entry_list_url, {"mesthiri": self.mesthiri_a.id, "date": "2026-09-10", "wage": "1000", "paid_amount": "500"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_entry_cannot_be_created_for_unassigned_site(self):
        response = self.client.post(self.entry_list_url, {"mesthiri": self.mesthiri_a.id, "date": "2025-12-31", "wage": "1000", "paid_amount": "0"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
