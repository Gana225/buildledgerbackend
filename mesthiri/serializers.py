from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from .models import MesthiriPayment
from .models import Mesthiri, MesthiriAssignment, MesthiriEntry


class MesthiriSerializer(serializers.ModelSerializer):
    current_site = serializers.SerializerMethodField()
    current_site_name = serializers.SerializerMethodField()

    class Meta:
        model = Mesthiri
        fields = ["id", "name", "is_active", "current_site", "current_site_name", "created_at", "updated_at"]
        read_only_fields = ["id", "current_site", "current_site_name", "created_at", "updated_at"]

    def get_current_assignment(self, obj):
        if not hasattr(obj, "_current_assignment_cache"):
            obj._current_assignment_cache = (
                obj.assignments.filter(end_date__isnull=True)
                .select_related("site").order_by("-start_date", "-id").first()
            )
        return obj._current_assignment_cache

    def get_current_site(self, obj):
        assignment = self.get_current_assignment(obj)
        return assignment.site_id if assignment else None

    def get_current_site_name(self, obj):
        assignment = self.get_current_assignment(obj)
        return assignment.site.name if assignment else None


class MesthiriAssignmentSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source="site.name", read_only=True)
    mesthiri_name = serializers.CharField(source="mesthiri.name", read_only=True)

    class Meta:
        model = MesthiriAssignment
        fields = ["id", "mesthiri", "mesthiri_name", "site", "site_name", "start_date", "end_date", "created_at", "updated_at"]
        read_only_fields = ["id", "mesthiri", "mesthiri_name", "site_name", "created_at", "updated_at"]

    def validate_site(self, site):
        if site.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("You cannot assign mesthiri to another user's site.")
        return site

    def validate(self, attrs):
        mesthiri = self.context.get("mesthiri") or getattr(self.instance, "mesthiri", None)
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be earlier than start date."})

        assignments = MesthiriAssignment.objects.filter(mesthiri=mesthiri)
        if self.instance:
            assignments = assignments.exclude(pk=self.instance.pk)
        overlapping = assignments.filter(Q(end_date__isnull=True) | Q(end_date__gte=start_date))
        if end_date:
            overlapping = overlapping.filter(start_date__lte=end_date)

        if not self.instance:
            closable_open = overlapping.filter(end_date__isnull=True, start_date__lt=start_date)
            other_overlaps = overlapping.exclude(pk__in=closable_open.values_list("pk", flat=True))
            if other_overlaps.exists():
                raise serializers.ValidationError("This assignment overlaps an existing assignment.")
            if closable_open.count() > 1:
                raise serializers.ValidationError("Multiple open assignments exist for this mesthiri.")
        elif overlapping.exists():
            raise serializers.ValidationError("This assignment overlaps an existing assignment.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        mesthiri = self.context["mesthiri"]
        start_date = validated_data["start_date"]
        previous_assignment = (MesthiriAssignment.objects.select_for_update()
            .filter(mesthiri=mesthiri, end_date__isnull=True, start_date__lt=start_date)
            .order_by("-start_date").first())
        if previous_assignment:
            previous_assignment.end_date = start_date - timedelta(days=1)
            previous_assignment.save(update_fields=["end_date", "updated_at"])
        return MesthiriAssignment.objects.create(mesthiri=mesthiri, **validated_data)


class MesthiriEntrySerializer(serializers.ModelSerializer):
    mesthiri_name = serializers.CharField(source="mesthiri.name", read_only=True)
    site_name = serializers.CharField(source="site.name", read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = MesthiriEntry
        fields = ["id", "mesthiri", "mesthiri_name", "site", "site_name", "date", "wage", "paid_amount", "remaining_amount", "created_at", "updated_at"]
        read_only_fields = ["id", "site", "site_name", "mesthiri_name", "remaining_amount", "created_at", "updated_at"]

    def validate_mesthiri(self, mesthiri):
        if mesthiri.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("You cannot use another user's mesthiri.")
        return mesthiri

    def validate(self, attrs):
        mesthiri = attrs.get("mesthiri", getattr(self.instance, "mesthiri", None))
        entry_date = attrs.get("date", getattr(self.instance, "date", None))
        wage = attrs.get("wage", getattr(self.instance, "wage", None))
        paid_amount = attrs.get("paid_amount", getattr(self.instance, "paid_amount", 0))
        if wage is not None and wage < 0:
            raise serializers.ValidationError({"wage": "Wage cannot be negative."})
        if paid_amount is not None and paid_amount < 0:
            raise serializers.ValidationError({"paid_amount": "Paid amount cannot be negative."})
        if wage is not None and paid_amount is not None and paid_amount > wage:
            raise serializers.ValidationError({"paid_amount": "Paid amount cannot exceed wage."})

        assignment = (MesthiriAssignment.objects.filter(mesthiri=mesthiri, start_date__lte=entry_date)
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=entry_date)).select_related("site").first())
        if not assignment:
            raise serializers.ValidationError({"date": "This mesthiri was not assigned to any site on this date."})
        requested_site = self.context.get("site")
        if requested_site and assignment.site_id != requested_site.id:
            raise serializers.ValidationError({"date": f"{mesthiri.name} was assigned to {assignment.site.name} on {entry_date}."})

        duplicate_entries = MesthiriEntry.objects.filter(mesthiri=mesthiri, date=entry_date)
        if self.instance:
            duplicate_entries = duplicate_entries.exclude(pk=self.instance.pk)
        if duplicate_entries.exists():
            raise serializers.ValidationError({"date": "An entry already exists for this mesthiri on this date."})
        attrs["_resolved_site"] = assignment.site
        return attrs

    def create(self, validated_data):
        return MesthiriEntry.objects.create(site=validated_data.pop("_resolved_site"), **validated_data)

    def update(self, instance, validated_data):
        instance.site = validated_data.pop("_resolved_site", instance.site)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class MesthiriPaymentSerializer(serializers.ModelSerializer):

    mesthiri_name = serializers.CharField(
        source="mesthiri.name",
        read_only=True,
    )

    site_name = serializers.CharField(
        source="site.name",
        read_only=True,
    )

    class Meta:
        model = MesthiriPayment

        fields = [
            "id",
            "mesthiri",
            "mesthiri_name",
            "site",
            "site_name",
            "payment_date",
            "amount",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "mesthiri_name",
            "site_name",
            "site",
            "created_at",
            "updated_at",
        ]