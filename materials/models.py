from django.db import models

from sites.models import Site


class Material(models.Model):

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="materials",
    )

    serial_number = models.PositiveIntegerField()

    name = models.CharField(max_length=200)

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    unit = models.CharField(max_length=50)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    purchase_date = models.DateField()

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["serial_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["site", "serial_number"],
                name="unique_material_serial_per_site",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="material_quantity_is_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="material_price_is_not_negative",
            ),
        ]

    def save(self, *args, **kwargs):

        if not self.serial_number:
            last_material = (
                Material.objects
                .filter(site=self.site)
                .order_by("-serial_number")
                .first()
            )

            if last_material:
                self.serial_number = (
                    last_material.serial_number + 1
                )
            else:
                self.serial_number = 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.serial_number} - {self.name}"
