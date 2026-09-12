from decimal import Decimal

from django.db.models import Sum

from labour.models import LabourEntry, LabourPayment
from mesthiri.models import MesthiriEntry, MesthiriPayment
from materials.models import Material


ZERO = Decimal("0.00")


def get_labour_totals(
    site,
    start_date=None,
    end_date=None,
):
    entries = LabourEntry.objects.filter(site=site)
    payments = LabourPayment.objects.filter(site=site)

    if start_date:
        entries = entries.filter(date__gte=start_date)
        payments = payments.filter(payment_date__gte=start_date)

    if end_date:
        entries = entries.filter(date__lte=end_date)
        payments = payments.filter(payment_date__lte=end_date)

    total_wage = (
        entries.aggregate(value=Sum("wage"))["value"]
        or ZERO
    )

    total_paid = (
        payments.aggregate(value=Sum("amount"))["value"]
        or ZERO
    )

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
    entries = MesthiriEntry.objects.filter(site=site)
    payments = MesthiriPayment.objects.filter(site=site)

    if start_date:
        entries = entries.filter(date__gte=start_date)
        payments = payments.filter(payment_date__gte=start_date)

    if end_date:
        entries = entries.filter(date__lte=end_date)
        payments = payments.filter(payment_date__lte=end_date)

    total_wage = (
        entries.aggregate(value=Sum("wage"))["value"]
        or ZERO
    )

    total_paid = (
        payments.aggregate(value=Sum("amount"))["value"]
        or ZERO
    )

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
    queryset = Material.objects.filter(site=site)

    if start_date:
        queryset = queryset.filter(
            purchase_date__gte=start_date
        )

    if end_date:
        queryset = queryset.filter(
            purchase_date__lte=end_date
        )

    total_price = (
        queryset.aggregate(value=Sum("price"))["value"]
        or ZERO
    )

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
