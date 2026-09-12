from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from sites.models import Site


class Labour(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="labours",
    )

    name = models.CharField(max_length=150)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_labour_name_per_user",
            )
        ]

    def __str__(self):
        return self.name


class LabourAssignment(models.Model):

    labour = models.ForeignKey(
        Labour,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="labour_assignments",
    )

    start_date = models.DateField()

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "-start_date",
            "-id",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "labour",
                    "site",
                    "start_date",
                ],
                name="unique_labour_assignment_start",
            ),
        ]

    def __str__(self):

        if self.end_date:
            return (
                f"{self.labour.name} - "
                f"{self.site.name} - "
                f"{self.start_date} to "
                f"{self.end_date}"
            )

        return (
            f"{self.labour.name} - "
            f"{self.site.name} - "
            f"{self.start_date} onwards"
        )

    def clean(self):

        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({
                "end_date": "End date cannot be before start date."
            })

        overlapping = LabourAssignment.objects.filter(
            labour=self.labour,
            start_date__lte=(
                self.end_date
                if self.end_date
                else "9999-12-31"
            ),
        )

        if self.end_date:
            overlapping = overlapping.filter(
                end_date__gte=self.start_date
            )
        else:
            overlapping = overlapping.filter(
                models.Q(end_date__isnull=True)
                | models.Q(end_date__gte=self.start_date)
            )

        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError(
                "This labour already has another "
                "assignment during this period."
            )


class LabourEntry(models.Model):

    labour = models.ForeignKey(
        Labour,
        on_delete=models.CASCADE,
        related_name="entries",
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="labour_entries",
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
                    "labour",
                    "date",
                ],
                name="unique_labour_entry_per_day",
            ),
            models.CheckConstraint(
                condition=models.Q(wage__gte=0),
                name="labour_entry_wage_is_valid",
            ),
        ]

    def __str__(self):
        return (
            f"{self.labour.name} - "
            f"{self.date} - "
            f"{self.site.name}"
        )


class LabourPayment(models.Model):

    labour = models.ForeignKey(
        Labour,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="labour_payments",
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
                name="labour_payment_amount_positive",
            ),
        ]

    def __str__(self):
        return (
            f"{self.labour.name} - "
            f"{self.site.name} - "
            f"₹{self.amount}"
        )