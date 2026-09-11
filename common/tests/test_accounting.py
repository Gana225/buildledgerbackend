from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from common.services.accounting import get_site_totals
from labour.models import Labour, LabourAssignment, LabourEntry
from materials.models import Material
from mesthiri.models import Mesthiri, MesthiriAssignment, MesthiriEntry
from sites.models import Site

User = get_user_model()


class AccountingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="accounting", email="accounting@example.com", password="TestPassword123!")
        self.site = Site.objects.create(user=self.user, name="Accounting Site")
        self.other_site = Site.objects.create(user=self.user, name="Other Site")
        self.labour = Labour.objects.create(user=self.user, name="Ramesh")
        self.mesthiri = Mesthiri.objects.create(user=self.user, name="Raju")
        LabourAssignment.objects.create(labour=self.labour, site=self.site, start_date=date(2026, 1, 1))
        MesthiriAssignment.objects.create(mesthiri=self.mesthiri, site=self.site, start_date=date(2026, 1, 1))

    def test_site_totals_are_balanced(self):
        LabourEntry.objects.create(labour=self.labour, site=self.site, date="2026-09-01", wage=Decimal("1000"), paid_amount=Decimal("600"))
        MesthiriEntry.objects.create(mesthiri=self.mesthiri, site=self.site, date="2026-09-01", wage=Decimal("1500"), paid_amount=Decimal("1000"))
        Material.objects.create(site=self.site, name="Cement", quantity=Decimal("10"), unit="bags", price=Decimal("5000"), purchase_date="2026-09-01")

        result = get_site_totals(self.site)
        self.assertEqual(result["total_expense"], Decimal("7500"))
        self.assertEqual(result["total_paid"], Decimal("6600"))
        self.assertEqual(result["total_outstanding"], Decimal("900"))
        self.assertEqual(result["total_expense"] - result["total_paid"], result["total_outstanding"])

    def test_historical_entry_stays_with_its_recorded_site(self):
        LabourEntry.objects.create(labour=self.labour, site=self.site, date="2026-09-01", wage=Decimal("1000"), paid_amount=Decimal("500"))
        LabourAssignment.objects.filter(labour=self.labour, site=self.site).update(end_date=date(2026, 9, 1))
        LabourAssignment.objects.create(labour=self.labour, site=self.other_site, start_date=date(2026, 9, 2))
        LabourEntry.objects.create(labour=self.labour, site=self.other_site, date="2026-09-02", wage=Decimal("2000"), paid_amount=Decimal("1500"))

        self.assertEqual(get_site_totals(self.site)["labour"]["total"], Decimal("1000"))
        self.assertEqual(get_site_totals(self.other_site)["labour"]["total"], Decimal("2000"))

    def test_date_range_limits_all_categories(self):
        LabourEntry.objects.create(labour=self.labour, site=self.site, date="2026-09-01", wage=Decimal("1000"), paid_amount=Decimal("500"))
        LabourEntry.objects.create(labour=self.labour, site=self.site, date="2026-09-10", wage=Decimal("2000"), paid_amount=Decimal("1500"))
        result = get_site_totals(self.site, start_date="2026-09-10", end_date="2026-09-10")
        self.assertEqual(result["total_expense"], Decimal("2000"))
        self.assertEqual(result["total_paid"], Decimal("1500"))
        self.assertEqual(result["total_outstanding"], Decimal("500"))
