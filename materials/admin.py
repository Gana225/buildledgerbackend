from django.contrib import admin

from .models import Material


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):

    list_display = [
        "serial_number",
        "name",
        "site",
        "quantity",
        "unit",
        "price",
        "purchase_date",
        "created_at",
    ]

    list_filter = [
        "site",
        "purchase_date",
    ]

    search_fields = [
        "name",
        "site__name",
        "site__code",
    ]