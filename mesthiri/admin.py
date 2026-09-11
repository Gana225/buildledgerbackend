from django.contrib import admin

from .models import Mesthiri, MesthiriAssignment, MesthiriEntry


@admin.register(Mesthiri)
class MesthiriAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "name",
        "current_site",
        "is_active",
        "created_at",
    ]

    list_filter = [
        "is_active",
    ]

    search_fields = [
        "name",
        "user__email",
    ]

    @admin.display(description="Current site")
    def current_site(self, obj):
        assignment = obj.assignments.filter(end_date__isnull=True).select_related("site").first()
        return assignment.site if assignment else None


@admin.register(MesthiriAssignment)
class MesthiriAssignmentAdmin(admin.ModelAdmin):
    list_display = ["id", "mesthiri", "site", "start_date", "end_date"]
    list_filter = ["site", "start_date", "end_date"]
    search_fields = ["mesthiri__name", "site__name", "site__code"]


@admin.register(MesthiriEntry)
class MesthiriEntryAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "mesthiri",
        "date",
        "wage",
        "paid_amount",
        "remaining",
    ]

    list_filter = [
        "date",
    ]

    search_fields = [
        "mesthiri__name",
    ]

    @admin.display(description="Remaining")
    def remaining(self, obj):
        return obj.wage - obj.paid_amount
