from django.contrib import admin

from .models import Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "code",
        "name",
        "user",
        "location",
        "is_active",
        "created_at",
    ]

    list_filter = [
        "is_active",
        "created_at",
    ]

    search_fields = [
        "code",
        "name",
        "location",
        "user__username",
    ]