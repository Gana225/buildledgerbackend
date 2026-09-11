# from decimal import Decimal

# from rest_framework import serializers

# from .models import Labour, LabourEntry


# class LabourSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = Labour

#         fields = [
#             "id",
#             "site",
#             "name",
#             "is_active",
#             "created_at",
#             "updated_at",
#         ]

#         read_only_fields = [
#             "id",
#             "site",
#             "created_at",
#             "updated_at",
#         ]


# class LabourEntrySerializer(serializers.ModelSerializer):

#     remaining_amount = serializers.DecimalField(
#         max_digits=12,
#         decimal_places=2,
#         read_only=True,
#     )

#     class Meta:
#         model = LabourEntry

#         fields = [
#             "id",
#             "labour",
#             "date",
#             "wage",
#             "paid_amount",
#             "remaining_amount",
#             "created_at",
#             "updated_at",
#         ]

#         read_only_fields = [
#             "id",
#             "remaining_amount",
#             "created_at",
#             "updated_at",
#         ]

#     def validate(self, attrs):
#         wage = attrs.get(
#             "wage",
#             getattr(self.instance, "wage", None),
#         )

#         paid_amount = attrs.get(
#             "paid_amount",
#             getattr(self.instance, "paid_amount", Decimal("0")),
#         )

#         if wage is not None and wage < 0:
#             raise serializers.ValidationError({
#                 "wage": "Wage cannot be negative."
#             })

#         if paid_amount is not None and paid_amount < 0:
#             raise serializers.ValidationError({
#                 "paid_amount": "Paid amount cannot be negative."
#             })

#         if (
#             wage is not None
#             and paid_amount is not None
#             and paid_amount > wage
#         ):
#             raise serializers.ValidationError({
#                 "paid_amount": "Paid amount cannot exceed the wage."
#             })

#         return attrs

#     def to_representation(self, instance):
#         data = super().to_representation(instance)

#         data["remaining_amount"] = str(
#             instance.wage - instance.paid_amount
#         )

#         return data


from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from sites.models import Site

from .models import (
    Labour,
    LabourAssignment,
    LabourEntry,
)


class LabourSerializer(serializers.ModelSerializer):

    current_site = serializers.SerializerMethodField()
    current_site_name = serializers.SerializerMethodField()

    class Meta:
        model = Labour
        fields = [
            "id",
            "name",
            "is_active",
            "current_site",
            "current_site_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "current_site",
            "current_site_name",
            "created_at",
            "updated_at",
        ]

    def get_current_assignment(self, obj):
        if hasattr(obj, "_current_assignment_cache"):
            return obj._current_assignment_cache

        assignment = (
            obj.assignments
            .filter(end_date__isnull=True)
            .select_related("site")
            .order_by("-start_date", "-id")
            .first()
        )

        obj._current_assignment_cache = assignment

        return assignment

    def get_current_site(self, obj):
        assignment = self.get_current_assignment(obj)

        if not assignment:
            return None

        return assignment.site_id

    def get_current_site_name(self, obj):
        assignment = self.get_current_assignment(obj)

        if not assignment:
            return None

        return assignment.site.name


class LabourAssignmentSerializer(serializers.ModelSerializer):

    site_name = serializers.CharField(
        source="site.name",
        read_only=True,
    )

    labour_name = serializers.CharField(
        source="labour.name",
        read_only=True,
    )

    class Meta:
        model = LabourAssignment
        fields = [
            "id",
            "labour",
            "labour_name",
            "site",
            "site_name",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "labour",
            "labour_name",
            "site_name",
            "created_at",
            "updated_at",
        ]

    def validate_site(self, site):
        request = self.context["request"]

        if site.user_id != request.user.id:
            raise serializers.ValidationError(
                "You cannot assign labour to another user's site."
            )

        return site

    def validate(self, attrs):

        labour = self.context.get("labour")

        if labour is None and self.instance:
            labour = self.instance.labour

        start_date = attrs.get(
            "start_date",
            getattr(self.instance, "start_date", None),
        )

        end_date = attrs.get(
            "end_date",
            getattr(self.instance, "end_date", None),
        )

        if end_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": (
                    "End date cannot be earlier than start date."
                )
            })

        assignments = LabourAssignment.objects.filter(
            labour=labour
        )

        if self.instance:
            assignments = assignments.exclude(
                pk=self.instance.pk
            )

        if end_date:
            overlapping = assignments.filter(
                start_date__lte=end_date,
            ).filter(
                Q(end_date__isnull=True)
                | Q(end_date__gte=start_date)
            )
        else:
            overlapping = assignments.filter(
                Q(end_date__isnull=True)
                | Q(end_date__gte=start_date)
            )

        if not self.instance:

            closable_open = overlapping.filter(
                end_date__isnull=True,
                start_date__lt=start_date,
            )

            other_overlaps = overlapping.exclude(
                pk__in=closable_open.values_list(
                    "pk",
                    flat=True,
                )
            )

            if other_overlaps.exists():
                raise serializers.ValidationError(
                    "This assignment overlaps an existing assignment."
                )

            if closable_open.count() > 1:
                raise serializers.ValidationError(
                    "Multiple open assignments exist for this labour."
                )

        elif overlapping.exists():

            raise serializers.ValidationError(
                "This assignment overlaps an existing assignment."
            )

        #
        # When creating a NEW assignment, an existing
        # open assignment that started before the new one
        # is allowed because it will automatically be closed.
        #
        if not self.instance:

            allowed_open = overlapping.filter(
                end_date__isnull=True,
                start_date__lt=start_date,
            )

            other_overlaps = overlapping.exclude(
                pk__in=allowed_open.values_list(
                    "pk",
                    flat=True,
                )
            )

            if other_overlaps.exists():
                raise serializers.ValidationError(
                    "This assignment overlaps an existing assignment."
                )

            if allowed_open.count() > 1:
                raise serializers.ValidationError(
                    "Multiple open assignments exist for this labour. "
                    "Please correct the assignment history first."
                )

        elif overlapping.exists():

            raise serializers.ValidationError(
                "This assignment overlaps an existing assignment."
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):

        labour = self.context["labour"]
        start_date = validated_data["start_date"]

        #
        # Automatically close the current open assignment.
        #
        previous_assignment = (
            LabourAssignment.objects
            .select_for_update()
            .filter(
                labour=labour,
                end_date__isnull=True,
                start_date__lt=start_date,
            )
            .order_by("-start_date")
            .first()
        )

        if previous_assignment:
            previous_assignment.end_date = (
                start_date - timedelta(days=1)
            )

            previous_assignment.save(
                update_fields=[
                    "end_date",
                    "updated_at",
                ]
            )

        return LabourAssignment.objects.create(
            labour=labour,
            **validated_data,
        )


class LabourEntrySerializer(serializers.ModelSerializer):

    labour_name = serializers.CharField(
        source="labour.name",
        read_only=True,
    )

    site_name = serializers.CharField(
        source="site.name",
        read_only=True,
    )

    remaining_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = LabourEntry

        fields = [
            "id",
            "labour",
            "labour_name",
            "site",
            "site_name",
            "date",
            "wage",
            "paid_amount",
            "remaining_amount",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "site",
            "site_name",
            "labour_name",
            "remaining_amount",
            "created_at",
            "updated_at",
        ]

    def validate_labour(self, labour):

        request = self.context["request"]

        if labour.user_id != request.user.id:
            raise serializers.ValidationError(
                "You cannot use another user's labour."
            )

        return labour

    def validate(self, attrs):

        labour = attrs.get(
            "labour",
            getattr(self.instance, "labour", None),
        )

        entry_date = attrs.get(
            "date",
            getattr(self.instance, "date", None),
        )

        wage = attrs.get(
            "wage",
            getattr(self.instance, "wage", None),
        )

        paid_amount = attrs.get(
            "paid_amount",
            getattr(self.instance, "paid_amount", 0),
        )

        if wage is not None and wage < 0:
            raise serializers.ValidationError({
                "wage": "Wage cannot be negative."
            })

        if paid_amount is not None and paid_amount < 0:
            raise serializers.ValidationError({
                "paid_amount": (
                    "Paid amount cannot be negative."
                )
            })

        if (
            wage is not None
            and paid_amount is not None
            and paid_amount > wage
        ):
            raise serializers.ValidationError({
                "paid_amount": (
                    "Paid amount cannot exceed wage."
                )
            })

        #
        # Find the worker assignment for the entry date.
        #
        assignment = (
            LabourAssignment.objects
            .filter(
                labour=labour,
                start_date__lte=entry_date,
            )
            .filter(
                Q(end_date__isnull=True)
                | Q(end_date__gte=entry_date)
            )
            .select_related("site")
            .first()
        )

        if not assignment:
            raise serializers.ValidationError({
                "date": (
                    "This labour was not assigned to any site "
                    "on this date."
                )
            })

        #
        # If using a site-specific endpoint,
        # ensure the historical assignment matches it.
        #
        requested_site = self.context.get("site")

        if (
            requested_site
            and assignment.site_id != requested_site.id
        ):
            raise serializers.ValidationError({
                "date": (
                    f"{labour.name} was assigned to "
                    f"{assignment.site.name} on {entry_date}."
                )
            })

        duplicate_entries = LabourEntry.objects.filter(
            labour=labour,
            date=entry_date,
        )

        if self.instance:
            duplicate_entries = duplicate_entries.exclude(
                pk=self.instance.pk
            )

        if duplicate_entries.exists():
            raise serializers.ValidationError({
                "date": (
                    "An entry already exists for this labour "
                    "on this date."
                )
            })

        attrs["_resolved_site"] = assignment.site

        return attrs

    def create(self, validated_data):

        site = validated_data.pop("_resolved_site")

        return LabourEntry.objects.create(
            site=site,
            **validated_data,
        )

    def update(self, instance, validated_data):

        site = validated_data.pop(
            "_resolved_site",
            instance.site,
        )

        instance.site = site

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        return instance