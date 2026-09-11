from decimal import Decimal

from django.db.models import Sum

from labour.models import LabourEntry
from mesthiri.models import MesthiriEntry
from materials.models import Material


ZERO = Decimal("0.00")


def get_labour_totals(
    site,
    start_date=None,
    end_date=None,
):
    # Entries retain the site where the work was performed, even if the
    # worker is later reassigned. Reports must therefore use entry.site.
    queryset = LabourEntry.objects.filter(site=site)

    if start_date:
        queryset = queryset.filter(
            date__gte=start_date,
        )

    if end_date:
        queryset = queryset.filter(
            date__lte=end_date,
        )

    result = queryset.aggregate(
        total_wage=Sum("wage"),
        total_paid=Sum("paid_amount"),
    )

    total_wage = result["total_wage"] or ZERO
    total_paid = result["total_paid"] or ZERO

    return {
        "total_wage": total_wage,
        "total_paid": total_paid,
        "total_remaining": total_wage - total_paid,
    }


def get_mesthiri_totals(
    site,
    start_date=None,
    end_date=None,
):
    queryset = MesthiriEntry.objects.filter(site=site)

    if start_date:
        queryset = queryset.filter(
            date__gte=start_date,
        )

    if end_date:
        queryset = queryset.filter(
            date__lte=end_date,
        )

    result = queryset.aggregate(
        total_wage=Sum("wage"),
        total_paid=Sum("paid_amount"),
    )

    total_wage = result["total_wage"] or ZERO
    total_paid = result["total_paid"] or ZERO

    return {
        "total_wage": total_wage,
        "total_paid": total_paid,
        "total_remaining": total_wage - total_paid,
    }


def get_material_totals(
    site,
    start_date=None,
    end_date=None,
):
    queryset = Material.objects.filter(
        site=site,
    )

    if start_date:
        queryset = queryset.filter(
            purchase_date__gte=start_date,
        )

    if end_date:
        queryset = queryset.filter(
            purchase_date__lte=end_date,
        )

    result = queryset.aggregate(
        total_price=Sum("price"),
    )

    total_price = result["total_price"] or ZERO

    return {
        "total_price": total_price,
    }


def get_site_totals(
    site,
    start_date=None,
    end_date=None,
):
    labour = get_labour_totals(
        site,
        start_date,
        end_date,
    )

    mesthiri = get_mesthiri_totals(
        site,
        start_date,
        end_date,
    )

    materials = get_material_totals(
        site,
        start_date,
        end_date,
    )

    total_expense = (
        labour["total_wage"]
        + mesthiri["total_wage"]
        + materials["total_price"]
    )

    total_paid = (
        labour["total_paid"]
        + mesthiri["total_paid"]
        # A material purchase is paid at the time it is recorded. Unlike
        # labour and mesthiri entries, it has no outstanding balance field.
        + materials["total_price"]
    )

    total_outstanding = (
        labour["total_remaining"]
        + mesthiri["total_remaining"]
    )

    return {
        "labour": {
            "total": labour["total_wage"],
            "paid": labour["total_paid"],
            "remaining": labour["total_remaining"],
        },

        "mesthiri": {
            "total": mesthiri["total_wage"],
            "paid": mesthiri["total_paid"],
            "remaining": mesthiri["total_remaining"],
        },

        "materials": {
            "total": materials["total_price"],
        },

        "total_expense": total_expense,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
    }
