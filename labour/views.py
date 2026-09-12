from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.db import models
from django.utils.dateparse import parse_date

from rest_framework import generics
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sites.models import Site

from mesthiri.models import (
    Mesthiri,
    MesthiriAssignment,
    MesthiriEntry,
)

from .models import (
    Labour,
    LabourAssignment,
    LabourEntry,
    LabourPayment,
    DailySiteWork
)

from .serializers import (
    LabourSerializer,
    LabourAssignmentSerializer,
    LabourEntrySerializer,
    LabourPaymentSerializer,
)

class LabourListCreateView(generics.ListCreateAPIView):

    serializer_class = LabourSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        queryset = (
            Labour.objects
            .filter(user=self.request.user)
            .prefetch_related("assignments__site")
        )

        site_id = self.request.query_params.get(
            "site"
        )

        active = self.request.query_params.get(
            "active"
        )

        if site_id:
            queryset = queryset.filter(
                assignments__site_id=site_id,
                assignments__end_date__isnull=True,
            )

        if active is not None:
            active_value = active.lower() in [
                "true",
                "1",
                "yes",
            ]

            queryset = queryset.filter(
                is_active=active_value
            )

        return queryset.distinct()

    def perform_create(self, serializer):

        serializer.save(
            user=self.request.user
        )


class LabourDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = LabourSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Labour.objects.filter(
            user=self.request.user
        )


class LabourAssignmentListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = LabourAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_labour(self):

        try:
            return Labour.objects.get(
                pk=self.kwargs["labour_id"],
                user=self.request.user,
            )

        except Labour.DoesNotExist:
            raise NotFound(
                "Labour not found."
            )

    def get_queryset(self):

        labour = self.get_labour()

        return (
            LabourAssignment.objects
            .filter(labour=labour)
            .select_related(
                "labour",
                "site",
            )
        )

    def get_serializer_context(self):

        context = super().get_serializer_context()

        context["labour"] = self.get_labour()

        return context


class LabourAssignmentDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = LabourAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return (
            LabourAssignment.objects
            .filter(
                labour__user=self.request.user
            )
            .select_related(
                "labour",
                "site",
            )
        )


class LabourAssignmentOnDateView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, labour_id):

        entry_date = request.query_params.get(
            "date"
        )

        if not entry_date:
            return Response(
                {
                    "date": [
                        "This query parameter is required."
                    ]
                },
                status=400,
            )

        try:
            labour = Labour.objects.get(
                id=labour_id,
                user=request.user,
            )

        except Labour.DoesNotExist:
            raise NotFound(
                "Labour not found."
            )

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

            return Response(
                {
                    "labour": labour.id,
                    "labour_name": labour.name,
                    "date": entry_date,
                    "assignment": None,
                }
            )

        serializer = LabourAssignmentSerializer(
            assignment,
            context={
                "request": request,
                "labour": labour,
            },
        )

        return Response({
            "labour": labour.id,
            "labour_name": labour.name,
            "date": entry_date,
            "assignment": serializer.data,
        })


class LabourSiteEntryListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = LabourEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_site(self):

        try:
            return Site.objects.get(
                pk=self.kwargs["site_id"],
                user=self.request.user,
            )

        except Site.DoesNotExist:
            raise NotFound(
                "Site not found."
            )

    def get_queryset(self):

        site = self.get_site()

        queryset = (
            LabourEntry.objects
            .filter(
                site=site,
                labour__user=self.request.user,
            )
            .select_related(
                "labour",
                "site",
            )
        )

        date_value = self.request.query_params.get(
            "date"
        )

        start_date = self.request.query_params.get(
            "start_date"
        )

        end_date = self.request.query_params.get(
            "end_date"
        )

        if date_value:

            queryset = queryset.filter(
                date=date_value
            )

        if start_date:

            queryset = queryset.filter(
                date__gte=start_date
            )

        if end_date:

            queryset = queryset.filter(
                date__lte=end_date
            )

        return queryset

    def get_serializer_context(self):

        context = super().get_serializer_context()

        context["site"] = self.get_site()

        return context


class LabourEntryDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = LabourEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return (
            LabourEntry.objects
            .filter(
                labour__user=self.request.user
            )
            .select_related(
                "labour",
                "site",
            )
        )



class LabourPaymentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_site(self, site_id, user):
        try:
            return Site.objects.get(
                id=site_id,
                user=user,
            )
        except Site.DoesNotExist:
            raise NotFound("Site not found.")

    def get_labour(self, labour_id, user):
        try:
            return Labour.objects.get(
                id=labour_id,
                user=user,
            )
        except Labour.DoesNotExist:
            raise NotFound("Labour not found.")

    def get(self, request, site_id, labour_id):
        site = self.get_site(
            site_id,
            request.user,
        )

        labour = self.get_labour(
            labour_id,
            request.user,
        )

        payments = (
            LabourPayment.objects
            .filter(
                site=site,
                labour=labour,
            )
            .select_related(
                "labour",
                "site",
            )
        )

        return Response(
            LabourPaymentSerializer(
                payments,
                many=True,
            ).data
        )

    @transaction.atomic
    def post(self, request, site_id, labour_id):
        site = self.get_site(
            site_id,
            request.user,
        )

        labour = self.get_labour(
            labour_id,
            request.user,
        )

        payment_date = request.data.get(
            "payment_date"
        )

        amount = request.data.get(
            "amount"
        )

        notes = request.data.get(
            "notes",
            "",
        )

        if not payment_date:
            raise ValidationError({
                "payment_date":
                    "Payment date is required."
            })

        if amount in [None, ""]:
            raise ValidationError({
                "amount":
                    "Payment amount is required."
            })

        try:
            from decimal import Decimal

            amount_value = Decimal(
                str(amount)
            )

        except Exception:
            raise ValidationError({
                "amount":
                    "Enter a valid payment amount."
            })

        if amount_value <= 0:
            raise ValidationError({
                "amount":
                    "Payment amount must be greater than zero."
            })

        earned = (
            LabourEntry.objects
            .filter(
                site=site,
                labour=labour,
            )
            .aggregate(
                total=models.Sum("wage")
            )["total"]
            or Decimal("0")
        )

        paid = (
            LabourPayment.objects
            .filter(
                site=site,
                labour=labour,
            )
            .aggregate(
                total=models.Sum("amount")
            )["total"]
            or Decimal("0")
        )

        outstanding = earned - paid

        if amount_value > outstanding:
            raise ValidationError({
                "amount":
                    f"Payment cannot exceed the "
                    f"outstanding amount of "
                    f"₹{outstanding:.2f}."
            })

        payment = LabourPayment.objects.create(
            labour=labour,
            site=site,
            payment_date=payment_date,
            amount=amount_value,
            notes=notes,
        )

        return Response(
            LabourPaymentSerializer(
                payment
            ).data,
            status=201,
        )

class LabourAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, site_id, labour_id):

        try:
            site = Site.objects.get(
                id=site_id,
                user=request.user,
            )
        except Site.DoesNotExist:
            raise NotFound("Site not found.")

        try:
            labour = Labour.objects.get(
                id=labour_id,
                user=request.user,
            )
        except Labour.DoesNotExist:
            raise NotFound("Labour not found.")

        contributions = (
            LabourEntry.objects
            .filter(
                site=site,
                labour=labour,
            )
            .order_by("-date", "-id")
        )
        
        daily_work_map = {
            item.date: item.work_description
            for item in DailySiteWork.objects.filter(
                site=site,
                date__in=[
                    contribution.date
                    for contribution in contributions
                ],
            )
        }

        payments = (
            LabourPayment.objects
            .filter(
                site=site,
                labour=labour,
            )
            .order_by(
                "-payment_date",
                "-id",
            )
        )

        from decimal import Decimal

        total_earned = sum(
            (
                entry.wage
                for entry in contributions
            ),
            Decimal("0"),
        )

        total_paid = sum(
            (
                payment.amount
                for payment in payments
            ),
            Decimal("0"),
        )

        total_due = (
            total_earned -
            total_paid
        )
        
        return Response({
            "labour": {
                "id": labour.id,
                "name": labour.name,
            },

            "site": {
                "id": site.id,
                "code": site.code,
                "name": site.name,
            },

            "summary": {
                "worked_days": contributions.count(),
                "total_earned": str(
                    total_earned
                ),
                "total_paid": str(
                    total_paid
                ),
                "total_due": str(
                    total_due
                ),
            },


            "contributions": [
                {
                    "id": entry.id,
                    "date": entry.date,
                    "wage": str(entry.wage),
                    "work_description": daily_work_map.get(
                        entry.date,
                        "",
                    ),
                }
                for entry in contributions
            ],

            "payments": [
                {
                    "id": payment.id,
                    "payment_date":
                        payment.payment_date,
                    "amount":
                        str(payment.amount),
                    "notes":
                        payment.notes,
                }
                for payment in payments
            ],
        })

class DailyWorkView(APIView):
    permission_classes = [IsAuthenticated]

    # ======================================================
    # SITE
    # ======================================================

    def get_site(self, site_id, user):
        try:
            return Site.objects.get(
                id=site_id,
                user=user,
            )
        except Site.DoesNotExist:
            raise NotFound("Site not found.")

    # ======================================================
    # DATE
    # ======================================================

    def parse_request_date(
        self,
        request,
        from_body=False,
    ):
        date_value = (
            request.data.get("date")
            if from_body
            else request.query_params.get("date")
        )

        if not date_value:
            raise ValidationError({
                "date": "This field is required."
            })

        entry_date = parse_date(str(date_value))

        if entry_date is None:
            raise ValidationError({
                "date": "Use YYYY-MM-DD format."
            })

        return entry_date

    # ======================================================
    # RESPONSE
    # ======================================================

    def build_response(
        self,
        request,
        site,
        entry_date,
    ):
        # --------------------------------------------------
        # Today's entries at this site
        # --------------------------------------------------
        
        daily_site_work, _ = DailySiteWork.objects.get_or_create(
            site=site,
            date=entry_date,
        )

        labour_entries = (
            LabourEntry.objects
            .filter(
                site=site,
                date=entry_date,
                labour__user=request.user,
            )
            .select_related("labour")
        )

        labour_entry_map = {
            entry.labour_id: entry
            for entry in labour_entries
        }

        mesthiri_entries = (
            MesthiriEntry.objects
            .filter(
                site=site,
                date=entry_date,
                mesthiri__user=request.user,
            )
            .select_related("mesthiri")
        )

        mesthiri_entry_map = {
            entry.mesthiri_id: entry
            for entry in mesthiri_entries
        }

        # --------------------------------------------------
        # People assigned to another site on this date
        # --------------------------------------------------

        labour_assigned_elsewhere_ids = set(
            LabourAssignment.objects
            .filter(
                labour__user=request.user,
                start_date__lte=entry_date,
            )
            .filter(
                Q(end_date__isnull=True)
                | Q(end_date__gte=entry_date)
            )
            .exclude(site_id=site.id)
            .values_list(
                "labour_id",
                flat=True,
            )
            .distinct()
        )

        mesthiri_assigned_elsewhere_ids = set(
            MesthiriAssignment.objects
            .filter(
                mesthiri__user=request.user,
                start_date__lte=entry_date,
            )
            .filter(
                Q(end_date__isnull=True)
                | Q(end_date__gte=entry_date)
            )
            .exclude(site_id=site.id)
            .values_list(
                "mesthiri_id",
                flat=True,
            )
            .distinct()
        )

        # --------------------------------------------------
        # People already working at another site on this date
        # --------------------------------------------------

        labour_entry_elsewhere_ids = set(
            LabourEntry.objects
            .filter(
                labour__user=request.user,
                date=entry_date,
            )
            .exclude(site_id=site.id)
            .values_list(
                "labour_id",
                flat=True,
            )
            .distinct()
        )

        mesthiri_entry_elsewhere_ids = set(
            MesthiriEntry.objects
            .filter(
                mesthiri__user=request.user,
                date=entry_date,
            )
            .exclude(site_id=site.id)
            .values_list(
                "mesthiri_id",
                flat=True,
            )
            .distinct()
        )

        labour_unavailable_ids = (
            labour_assigned_elsewhere_ids
            | labour_entry_elsewhere_ids
        )

        mesthiri_unavailable_ids = (
            mesthiri_assigned_elsewhere_ids
            | mesthiri_entry_elsewhere_ids
        )

        # --------------------------------------------------
        # Available Labour
        #
        # Current-site workers and unassigned workers are
        # available. Workers assigned/working elsewhere are
        # hidden. Existing current-site entries go to Today.
        # --------------------------------------------------

        labour_queryset = (
            Labour.objects
            .filter(
                user=request.user,
                is_active=True,
            )
            .exclude(
                id__in=labour_unavailable_ids
            )
            .order_by("name")
        )

        available_labour = []
        today_labour = []

        for labour in labour_queryset:
            entry = labour_entry_map.get(labour.id)

            if entry:
                today_labour.append({
                    "entry_id": entry.id,
                    "labour_id": labour.id,
                    "name": labour.name,
                    "wage": str(entry.wage),
                })
            else:
                available_labour.append({
                    "id": labour.id,
                    "name": labour.name,
                })

        # --------------------------------------------------
        # Available Mesthiri
        # --------------------------------------------------

        mesthiri_queryset = (
            Mesthiri.objects
            .filter(
                user=request.user,
                is_active=True,
            )
            .exclude(
                id__in=mesthiri_unavailable_ids
            )
            .order_by("name")
        )

        available_mesthiri = []
        today_mesthiri = []

        for mesthiri in mesthiri_queryset:
            entry = mesthiri_entry_map.get(mesthiri.id)

            if entry:
                today_mesthiri.append({
                    "entry_id": entry.id,
                    "mesthiri_id": mesthiri.id,
                    "name": mesthiri.name,
                    "wage": str(entry.wage),
                })
            else:
                available_mesthiri.append({
                    "id": mesthiri.id,
                    "name": mesthiri.name,
                })

        # --------------------------------------------------
        # Daily work totals
        #
        # Payments are intentionally NOT included here.
        # --------------------------------------------------

        labour_total = sum(
            (entry.wage for entry in labour_entries),
            Decimal("0.00"),
        )

        mesthiri_total = sum(
            (entry.wage for entry in mesthiri_entries),
            Decimal("0.00"),
        )

        total = labour_total + mesthiri_total

        return {
            "site": {
                "id": site.id,
                "code": site.code,
                "name": site.name,
            },
            "date": entry_date,
            "work_description": daily_site_work.work_description,
            "available_labour": available_labour,
            "today_labour": today_labour,
            "available_mesthiri": available_mesthiri,
            "today_mesthiri": today_mesthiri,
            "summary": {
                "labour_total": str(labour_total),
                "mesthiri_total": str(mesthiri_total),
                "total": str(total),
            },
        }

    # ======================================================
    # GET
    # ======================================================

    def get(self, request, site_id):
        site = self.get_site(
            site_id,
            request.user,
        )

        entry_date = self.parse_request_date(
            request
        )

        return Response(
            self.build_response(
                request,
                site,
                entry_date,
            )
        )

    # ======================================================
    # POST
    # ======================================================

    @transaction.atomic
    def post(self, request, site_id):
        site = self.get_site(
            site_id,
            request.user,
        )

        entry_date = self.parse_request_date(
            request,
            from_body=True,
        )
        
        work_description = str(
            request.data.get("work_description", "")
        ).strip()

        labour_data = request.data.get(
            "labour",
            [],
        )

        mesthiri_data = request.data.get(
            "mesthiri",
            [],
        )

        if not isinstance(labour_data, list):
            raise ValidationError({
                "labour": "Must be a list."
            })

        if not isinstance(mesthiri_data, list):
            raise ValidationError({
                "mesthiri": "Must be a list."
            })

        # ==================================================
        # DUPLICATE CHECKS
        # ==================================================

        labour_ids = [
            item.get("labour")
            for item in labour_data
        ]

        if len(labour_ids) != len(set(labour_ids)):
            raise ValidationError({
                "labour":
                    "The same labour cannot be added twice."
            })

        mesthiri_ids = [
            item.get("mesthiri")
            for item in mesthiri_data
        ]

        if len(mesthiri_ids) != len(set(mesthiri_ids)):
            raise ValidationError({
                "mesthiri":
                    "The same mesthiri cannot be added twice."
            })

        # ==================================================
        # LABOUR
        # ==================================================

        saved_labour_ids = []

        for item in labour_data:
            labour_id = item.get("labour")

            if not labour_id:
                raise ValidationError({
                    "labour": "Labour ID is required."
                })

            try:
                labour = Labour.objects.get(
                    id=labour_id,
                    user=request.user,
                )
            except Labour.DoesNotExist:
                raise ValidationError({
                    "labour":
                        f"Labour {labour_id} does not exist."
                })

            # A worker assigned to another site cannot be
            # added here on the same date.
            assignment_elsewhere = (
                LabourAssignment.objects
                .filter(
                    labour=labour,
                    start_date__lte=entry_date,
                )
                .filter(
                    Q(end_date__isnull=True)
                    | Q(end_date__gte=entry_date)
                )
                .exclude(site_id=site.id)
                .select_related("site")
                .first()
            )

            if assignment_elsewhere:
                raise ValidationError({
                    "labour":
                        f"{labour.name} is assigned to "
                        f"{assignment_elsewhere.site.name} "
                        f"on {entry_date}."
                })

            # A worker can only have one daily work entry.
            entry_elsewhere = (
                LabourEntry.objects
                .filter(
                    labour=labour,
                    date=entry_date,
                )
                .exclude(site_id=site.id)
                .select_related("site")
                .first()
            )

            if entry_elsewhere:
                raise ValidationError({
                    "labour":
                        f"{labour.name} already has work "
                        f"at {entry_elsewhere.site.name} "
                        f"on {entry_date}."
                })

            wage = item.get("wage")

            if wage is None or str(wage).strip() == "":
                raise ValidationError({
                    "wage":
                        f"Wage is required for {labour.name}."
                })

            try:
                wage_value = Decimal(str(wage))
            except (TypeError, ValueError, ArithmeticError):
                raise ValidationError({
                    "wage":
                        f"Invalid wage for {labour.name}."
                })

            if wage_value < 0:
                raise ValidationError({
                    "wage":
                        f"Wage cannot be negative for "
                        f"{labour.name}."
                })

            existing_entry = (
                LabourEntry.objects
                .filter(
                    labour=labour,
                    date=entry_date,
                )
                .first()
            )

            if existing_entry:
                if existing_entry.site_id != site.id:
                    raise ValidationError({
                        "labour":
                            f"{labour.name} already has "
                            f"a daily entry at another site."
                    })

                existing_entry.wage = wage_value
                existing_entry.save(
                    update_fields=[
                        "wage",
                        "updated_at",
                    ]
                )
            else:
                LabourEntry.objects.create(
                    labour=labour,
                    site=site,
                    date=entry_date,
                    wage=wage_value,
                )

            saved_labour_ids.append(labour.id)

        # Remove people removed from today's list.
        LabourEntry.objects.filter(
            site=site,
            date=entry_date,
        ).exclude(
            labour_id__in=saved_labour_ids
        ).delete()

        # ==================================================
        # MESTHIRI
        # ==================================================

        saved_mesthiri_ids = []

        for item in mesthiri_data:
            mesthiri_id = item.get("mesthiri")

            if not mesthiri_id:
                raise ValidationError({
                    "mesthiri":
                        "Mesthiri ID is required."
                })

            try:
                mesthiri = Mesthiri.objects.get(
                    id=mesthiri_id,
                    user=request.user,
                )
            except Mesthiri.DoesNotExist:
                raise ValidationError({
                    "mesthiri":
                        f"Mesthiri {mesthiri_id} "
                        f"does not exist."
                })

            assignment_elsewhere = (
                MesthiriAssignment.objects
                .filter(
                    mesthiri=mesthiri,
                    start_date__lte=entry_date,
                )
                .filter(
                    Q(end_date__isnull=True)
                    | Q(end_date__gte=entry_date)
                )
                .exclude(site_id=site.id)
                .select_related("site")
                .first()
            )

            if assignment_elsewhere:
                raise ValidationError({
                    "mesthiri":
                        f"{mesthiri.name} is assigned to "
                        f"{assignment_elsewhere.site.name} "
                        f"on {entry_date}."
                })

            entry_elsewhere = (
                MesthiriEntry.objects
                .filter(
                    mesthiri=mesthiri,
                    date=entry_date,
                )
                .exclude(site_id=site.id)
                .select_related("site")
                .first()
            )

            if entry_elsewhere:
                raise ValidationError({
                    "mesthiri":
                        f"{mesthiri.name} already has work "
                        f"at {entry_elsewhere.site.name} "
                        f"on {entry_date}."
                })

            wage = item.get("wage")

            if wage is None or str(wage).strip() == "":
                raise ValidationError({
                    "wage":
                        f"Wage is required for "
                        f"{mesthiri.name}."
                })

            try:
                wage_value = Decimal(str(wage))
            except (TypeError, ValueError, ArithmeticError):
                raise ValidationError({
                    "wage":
                        f"Invalid wage for "
                        f"{mesthiri.name}."
                })

            if wage_value < 0:
                raise ValidationError({
                    "wage":
                        f"Wage cannot be negative for "
                        f"{mesthiri.name}."
                })

            existing_entry = (
                MesthiriEntry.objects
                .filter(
                    mesthiri=mesthiri,
                    date=entry_date,
                )
                .first()
            )

            if existing_entry:
                if existing_entry.site_id != site.id:
                    raise ValidationError({
                        "mesthiri":
                            f"{mesthiri.name} already has "
                            f"a daily entry at another site."
                    })

                existing_entry.wage = wage_value
                existing_entry.save(
                    update_fields=[
                        "wage",
                        "updated_at",
                    ]
                )
            else:
                MesthiriEntry.objects.create(
                    mesthiri=mesthiri,
                    site=site,
                    date=entry_date,
                    wage=wage_value,
                )

            saved_mesthiri_ids.append(mesthiri.id)

        # Remove people removed from today's list.
        MesthiriEntry.objects.filter(
            site=site,
            date=entry_date,
        ).exclude(
            mesthiri_id__in=saved_mesthiri_ids
        ).delete()
        
        daily_site_work, _ = DailySiteWork.objects.get_or_create(
            site=site,
            date=entry_date,
        )

        daily_site_work.work_description = work_description
        daily_site_work.save(
            update_fields=[
                "work_description",
                "updated_at",
            ]
)
        
        return Response(
            self.build_response(
                request,
                site,
                entry_date,
            )
        )