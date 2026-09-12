from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models, transaction
from sites.models import Site
from .models import Mesthiri, MesthiriAssignment, MesthiriEntry,MesthiriPayment
from .serializers import MesthiriAssignmentSerializer, MesthiriEntrySerializer, MesthiriSerializer, MesthiriPaymentSerializer


class MesthiriListCreateView(generics.ListCreateAPIView):
    serializer_class = MesthiriSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Mesthiri.objects.filter(user=self.request.user).prefetch_related("assignments__site")
        if site_id := self.request.query_params.get("site"):
            queryset = queryset.filter(assignments__site_id=site_id, assignments__end_date__isnull=True)
        active = self.request.query_params.get("active")
        if active is not None:
            queryset = queryset.filter(is_active=active.lower() in ["true", "1", "yes"])
        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MesthiriDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MesthiriSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Mesthiri.objects.filter(user=self.request.user)


class MesthiriAssignmentListCreateView(generics.ListCreateAPIView):
    serializer_class = MesthiriAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_mesthiri(self):
        try:
            return Mesthiri.objects.get(pk=self.kwargs["mesthiri_id"], user=self.request.user)
        except Mesthiri.DoesNotExist:
            raise NotFound("Mesthiri not found.")

    def get_queryset(self):
        return MesthiriAssignment.objects.filter(mesthiri=self.get_mesthiri()).select_related("mesthiri", "site")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["mesthiri"] = self.get_mesthiri()
        return context


class MesthiriAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MesthiriAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MesthiriAssignment.objects.filter(mesthiri__user=self.request.user).select_related("mesthiri", "site")


class MesthiriAssignmentOnDateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, mesthiri_id):
        entry_date = request.query_params.get("date")
        if not entry_date:
            return Response({"date": ["This query parameter is required."]}, status=400)
        try:
            mesthiri = Mesthiri.objects.get(id=mesthiri_id, user=request.user)
        except Mesthiri.DoesNotExist:
            raise NotFound("Mesthiri not found.")
        assignment = (MesthiriAssignment.objects.filter(mesthiri=mesthiri, start_date__lte=entry_date)
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=entry_date)).select_related("site").first())
        return Response({
            "mesthiri": mesthiri.id,
            "mesthiri_name": mesthiri.name,
            "date": entry_date,
            "assignment": MesthiriAssignmentSerializer(assignment, context={"request": request, "mesthiri": mesthiri}).data if assignment else None,
        })


class MesthiriSiteEntryListCreateView(generics.ListCreateAPIView):
    serializer_class = MesthiriEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_site(self):
        try:
            return Site.objects.get(pk=self.kwargs["site_id"], user=self.request.user)
        except Site.DoesNotExist:
            raise NotFound("Site not found.")

    def get_queryset(self):
        queryset = MesthiriEntry.objects.filter(site=self.get_site(), mesthiri__user=self.request.user).select_related("mesthiri", "site")
        for param, lookup in [("date", "date"), ("start_date", "date__gte"), ("end_date", "date__lte")]:
            if value := self.request.query_params.get(param):
                queryset = queryset.filter(**{lookup: value})
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["site"] = self.get_site()
        return context


class MesthiriEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MesthiriEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MesthiriEntry.objects.filter(mesthiri__user=self.request.user).select_related("mesthiri", "site")


class MesthiriPaymentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_site(self, site_id, user):
        try:
            return Site.objects.get(
                id=site_id,
                user=user,
            )
        except Site.DoesNotExist:
            raise NotFound("Site not found.")

    def get_mesthiri(self, mesthiri_id, user):
        try:
            return Mesthiri.objects.get(
                id=mesthiri_id,
                user=user,
            )
        except Mesthiri.DoesNotExist:
            raise NotFound("Mesthiri not found.")

    def get(self, request, site_id, mesthiri_id):

        site = self.get_site(
            site_id,
            request.user,
        )

        mesthiri = self.get_mesthiri(
            mesthiri_id,
            request.user,
        )

        payments = (
            MesthiriPayment.objects
            .filter(
                site=site,
                mesthiri=mesthiri,
            )
            .select_related(
                "mesthiri",
                "site",
            )
        )

        return Response(
            MesthiriPaymentSerializer(
                payments,
                many=True,
            ).data
        )

    @transaction.atomic
    def post(self, request, site_id, mesthiri_id):

        site = self.get_site(
            site_id,
            request.user,
        )

        mesthiri = self.get_mesthiri(
            mesthiri_id,
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

        from decimal import Decimal

        try:
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
            MesthiriEntry.objects
            .filter(
                site=site,
                mesthiri=mesthiri,
            )
            .aggregate(
                total=models.Sum("wage")
            )["total"]
            or Decimal("0")
        )

        paid = (
            MesthiriPayment.objects
            .filter(
                site=site,
                mesthiri=mesthiri,
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

        payment = MesthiriPayment.objects.create(
            mesthiri=mesthiri,
            site=site,
            payment_date=payment_date,
            amount=amount_value,
            notes=notes,
        )

        return Response(
            MesthiriPaymentSerializer(
                payment
            ).data,
            status=201,
        )
        
class MesthiriAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, site_id, mesthiri_id):

        try:
            site = Site.objects.get(
                id=site_id,
                user=request.user,
            )
        except Site.DoesNotExist:
            raise NotFound("Site not found.")

        try:
            mesthiri = Mesthiri.objects.get(
                id=mesthiri_id,
                user=request.user,
            )
        except Mesthiri.DoesNotExist:
            raise NotFound("Mesthiri not found.")

        contributions = (
            MesthiriEntry.objects
            .filter(
                site=site,
                mesthiri=mesthiri,
            )
            .order_by("-date", "-id")
        )

        payments = (
            MesthiriPayment.objects
            .filter(
                site=site,
                mesthiri=mesthiri,
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
            "mesthiri": {
                "id": mesthiri.id,
                "name": mesthiri.name,
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