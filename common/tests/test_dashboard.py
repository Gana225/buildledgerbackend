from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from labour.models import Labour, LabourAssignment, LabourEntry
from materials.models import Material
from mesthiri.models import Mesthiri, MesthiriAssignment, MesthiriEntry
from sites.models import Site

User = get_user_model()


class DashboardTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dashboard", email="dashboard@example.com", password="TestPassword123!")
        self.other_user = User.objects.create_user(username="other_dashboard", email="other@example.com", password="TestPassword123!")
        self.site = Site.objects.create(user=self.user, name="Dashboard Site")
        self.empty_site = Site.objects.create(user=self.user, name="Empty Site")
        self.other_site = Site.objects.create(user=self.other_user, name="Other Site")
        labour = Labour.objects.create(user=self.user, name="Ramesh")
        mesthiri = Mesthiri.objects.create(user=self.user, name="Raju")
        LabourAssignment.objects.create(labour=labour, site=self.site, start_date=date(2026, 1, 1))
        MesthiriAssignment.objects.create(mesthiri=mesthiri, site=self.site, start_date=date(2026, 1, 1))
        LabourEntry.objects.create(labour=labour, site=self.site, date="2026-09-01", wage=Decimal("1000"), paid_amount=Decimal("600"))
        MesthiriEntry.objects.create(mesthiri=mesthiri, site=self.site, date="2026-09-01", wage=Decimal("1500"), paid_amount=Decimal("1000"))
        Material.objects.create(site=self.site, name="Cement", quantity=Decimal("10"), unit="bags", price=Decimal("5000"), purchase_date="2026-09-01")
        self.client.force_authenticate(user=self.user)

    def test_main_dashboard_is_user_scoped_and_balanced(self):
        response = self.client.get(reverse("main-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["site_count"], 2)
        self.assertEqual(response.data["summary"]["total_expense"], "7500.00")
        self.assertEqual(response.data["summary"]["total_paid"], "6600.00")
        self.assertEqual(response.data["summary"]["total_outstanding"], "900.00")
        self.assertNotIn(self.other_site.id, [site["site_id"] for site in response.data["sites"]])

    def test_site_dashboard_returns_daily_and_monthly_ledger_data(self):
        response = self.client.get(reverse("site-dashboard", kwargs={"site_id": self.site.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["total_expense"], "7500.00")
        self.assertEqual(response.data["labour_daily"][0]["total"], "1000.00")
        self.assertEqual(response.data["mesthiri_monthly"][0]["total"], "1500.00")
        self.assertEqual(response.data["material_daily"][0]["total"], "5000.00")

    def test_other_users_site_is_not_accessible(self):
        response = self.client.get(reverse("site-dashboard", kwargs={"site_id": self.other_site.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
