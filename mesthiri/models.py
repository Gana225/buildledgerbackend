from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from sites.models import Site


class Mesthiri(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mesthiris",
    )

    name = models.CharField(
        max_length=150,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "name",
                ],
                name="unique_mesthiri_name_per_user",
            )
        ]

    def __str__(self):
        return self.name


class MesthiriAssignment(models.Model):

    mesthiri = models.ForeignKey(
        Mesthiri,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="mesthiri_assignments",
    )

    start_date = models.DateField()

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-start_date",
            "-id",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "mesthiri",
                    "site",
                    "start_date",
                ],
                name="unique_mesthiri_assignment_start",
            ),
        ]

    def __str__(self):

        if self.end_date:
            return (
                f"{self.mesthiri.name} - "
                f"{self.site.name} - "
                f"{self.start_date} to "
                f"{self.end_date}"
            )

        return (
            f"{self.mesthiri.name} - "
            f"{self.site.name} - "
            f"{self.start_date} onwards"
        )

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({
                "end_date": "End date cannot be before start date."
            })

        overlapping = MesthiriAssignment.objects.filter(
            mesthiri=self.mesthiri,
            start_date__lte=(self.end_date or "9999-12-31"),
        )
        if self.end_date:
            overlapping = overlapping.filter(end_date__gte=self.start_date)
        else:
            overlapping = overlapping.filter(
                models.Q(end_date__isnull=True)
                | models.Q(end_date__gte=self.start_date)
            )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError(
                "This mesthiri already has another assignment during this period."
            )

class MesthiriEntry(models.Model):

    mesthiri = models.ForeignKey(
        Mesthiri,
        on_delete=models.CASCADE,
        related_name="entries",
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="mesthiri_entries",
    )

    date = models.DateField()

    wage = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-date",
            "-id",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "mesthiri",
                    "date",
                ],
                name="unique_mesthiri_entry_per_day",
            ),
            models.CheckConstraint(
                condition=models.Q(wage__gte=0),
                name="mesthiri_entry_wage_is_valid",
            ),
        ]

    def __str__(self):
        return (
            f"{self.mesthiri.name} - "
            f"{self.date} - "
            f"{self.site.name}"
        )


class MesthiriPayment(models.Model):

    mesthiri = models.ForeignKey(
        Mesthiri,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="mesthiri_payments",
    )

    payment_date = models.DateField()

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-payment_date",
            "-id",
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="mesthiri_payment_amount_positive",
            ),
        ]

    def __str__(self):
        return (
            f"{self.mesthiri.name} - "
            f"{self.site.name} - "
            f"₹{self.amount}"
        )