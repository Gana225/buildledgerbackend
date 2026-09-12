from django.contrib import admin

from .models import Labour, LabourAssignment, LabourEntry


@admin.register(Labour)
class LabourAdmin(admin.ModelAdmin):

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


@admin.register(LabourAssignment)
class LabourAssignmentAdmin(admin.ModelAdmin):
    list_display = ["id", "labour", "site", "start_date", "end_date"]
    list_filter = ["site", "start_date", "end_date"]
    search_fields = ["labour__name", "site__name", "site__code"]


@admin.register(LabourEntry)
class LabourEntryAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "labour",
        "date",
        "wage",
        "remaining",
    ]

    list_filter = [
        "date",
    ]

    search_fields = [
        "labour__name",
    ]

    @admin.display(
        description="Remaining"
    )
    def remaining(self, obj):
        return obj.wage - obj.paid_amount
