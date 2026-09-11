from django.conf import settings
from django.db import models


class Site(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sites",
    )

    code = models.CharField(max_length=20)

    name = models.CharField(max_length=200)

    location = models.CharField(
        max_length=255,
        blank=True,
    )

    description = models.TextField(
        blank=True,
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
        ordering = ["id"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "code"],
                name="unique_site_code_per_user",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.code:
            existing_codes = (
                Site.objects
                .filter(
                    user=self.user,
                    code__istartswith="S",
                )
                .values_list("code", flat=True)
            )

            numbers = []

            for code in existing_codes:
                try:
                    number = int(code[1:])
                    numbers.append(number)
                except (ValueError, TypeError):
                    continue

            next_number = max(numbers, default=0) + 1

            self.code = f"S{next_number}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"