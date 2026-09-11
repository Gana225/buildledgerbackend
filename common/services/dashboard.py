from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import TruncDate, TruncMonth

from labour.models import LabourEntry
from mesthiri.models import MesthiriEntry
from materials.models import Material
from sites.models import Site

from .accounting import get_site_totals


ZERO = Decimal("0.00")


def get_site_dashboard(site, start_date=None, end_date=None):
    totals = get_site_totals(
        site=site,
        start_date=start_date,
        end_date=end_date,
    )

    labour_queryset = LabourEntry.objects.filter(site=site)

    mesthiri_queryset = MesthiriEntry.objects.filter(site=site)

    material_queryset = Material.objects.filter(
        site=site
    )

    if start_date:
        labour_queryset = labour_queryset.filter(
            date__gte=start_date
        )
        mesthiri_queryset = mesthiri_queryset.filter(
            date__gte=start_date
        )
        material_queryset = material_queryset.filter(
            purchase_date__gte=start_date
        )

    if end_date:
        labour_queryset = labour_queryset.filter(
            date__lte=end_date
        )
        mesthiri_queryset = mesthiri_queryset.filter(
            date__lte=end_date
        )
        material_queryset = material_queryset.filter(
            purchase_date__lte=end_date
        )

    # -------------------------
    # Daily labour totals
    # -------------------------

    labour_daily = (
        labour_queryset
        .values("date")
        .annotate(
            total=Sum("wage"),
            paid=Sum("paid_amount"),
        )
        .order_by("date")
    )

    # -------------------------
    # Daily mesthiri totals
    # -------------------------

    mesthiri_daily = (
        mesthiri_queryset
        .values("date")
        .annotate(
            total=Sum("wage"),
            paid=Sum("paid_amount"),
        )
        .order_by("date")
    )

    # -------------------------
    # Daily material totals
    # -------------------------

    material_daily = (
        material_queryset
        .values("purchase_date")
        .annotate(
            total=Sum("price"),
        )
        .order_by("purchase_date")
    )

    # -------------------------
    # Monthly spending
    # -------------------------

    labour_monthly = (
        labour_queryset
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("wage"))
        .order_by("month")
    )

    mesthiri_monthly = (
        mesthiri_queryset
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Sum("wage"))
        .order_by("month")
    )

    material_monthly = (
        material_queryset
        .annotate(month=TruncMonth("purchase_date"))
        .values("month")
        .annotate(total=Sum("price"))
        .order_by("month")
    )

    return {
        "site": {
            "id": site.id,
            "code": site.code,
            "name": site.name,
        },

        "summary": totals,

        "expense_breakdown": [
            {
                "category": "Labour",
                "amount": totals["labour"]["total"],
            },
            {
                "category": "Mesthiri",
                "amount": totals["mesthiri"]["total"],
            },
            {
                "category": "Materials",
                "amount": totals["materials"]["total"],
            },
        ],

        "labour_daily": list(labour_daily),

        "mesthiri_daily": list(mesthiri_daily),

        "material_daily": list(material_daily),

        "labour_monthly": list(labour_monthly),

        "mesthiri_monthly": list(mesthiri_monthly),

        "material_monthly": list(material_monthly),
    }


def get_main_dashboard(user, start_date=None, end_date=None):
    sites = Site.objects.filter(
        user=user
    ).order_by("id")

    site_data = []

    total_labour = ZERO
    total_mesthiri = ZERO
    total_materials = ZERO

    total_expense = ZERO
    total_paid = ZERO
    total_outstanding = ZERO

    for site in sites:
        totals = get_site_totals(
            site=site,
            start_date=start_date,
            end_date=end_date,
        )

        total_labour += totals["labour"]["total"]
        total_mesthiri += totals["mesthiri"]["total"]
        total_materials += totals["materials"]["total"]

        total_expense += totals["total_expense"]
        total_paid += totals["total_paid"]
        total_outstanding += totals["total_outstanding"]

        site_data.append({
            "site_id": site.id,
            "site_code": site.code,
            "site_name": site.name,
            "total_expense": totals["total_expense"],
            "total_paid": totals["total_paid"],
            "total_outstanding": totals["total_outstanding"],
        })

    return {
        "site_count": sites.count(),

        "summary": {
            "labour": total_labour,
            "mesthiri": total_mesthiri,
            "materials": total_materials,
            "total_expense": total_expense,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
        },

        "expense_breakdown": [
            {
                "category": "Labour",
                "amount": total_labour,
            },
            {
                "category": "Mesthiri",
                "amount": total_mesthiri,
            },
            {
                "category": "Materials",
                "amount": total_materials,
            },
        ],

        "sites": site_data,
    }
