from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from sites.models import Site

from .filters import get_date_range
from .serializers import (
    SiteAccountingSerializer,
    SiteDashboardSerializer,
    MainDashboardSerializer,
)

from .services.dashboard import (
    get_site_dashboard,
    get_main_dashboard,
)
from .services.accounting import get_site_totals


class SiteAccountingView(
    generics.RetrieveAPIView
):

    permission_classes = [IsAuthenticated]
    serializer_class = SiteAccountingSerializer

    def get_queryset(self):
        return Site.objects.filter(
            user=self.request.user
        )

    def retrieve(self, request, *args, **kwargs):

        site = self.get_object()

        start_date, end_date = get_date_range(
            request
        )

        data = get_site_totals(
            site,
            start_date,
            end_date,
        )

        serializer = self.get_serializer(
            data
        )

        return Response(
            serializer.data
        )
    
class MainDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MainDashboardSerializer

    def get(self, request):
        start_date, end_date = get_date_range(request)

        data = get_main_dashboard(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
        )

        serializer = self.get_serializer(data)

        return Response(serializer.data)


class SiteDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SiteDashboardSerializer

    def get(self, request, site_id):
        site = get_object_or_404(
            Site.objects.filter(
                user=request.user
            ),
            id=site_id,
        )

        start_date, end_date = get_date_range(request)

        data = get_site_dashboard(
            site=site,
            start_date=start_date,
            end_date=end_date,
        )

        serializer = self.get_serializer(data)

        return Response(serializer.data)

from decimal import Decimal

from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sites.models import Site
from labour.models import Labour, LabourEntry, LabourPayment
from mesthiri.models import Mesthiri, MesthiriEntry, MesthiriPayment


class SiteWorkerAccountsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, site_id):

        try:
            site = Site.objects.get(
                id=site_id,
                user=request.user,
            )
        except Site.DoesNotExist:
            return Response(
                {"detail": "Site not found."},
                status=404,
            )

        labour = (
            Labour.objects
            .filter(
                user=request.user,
                is_active=True,
                entries__site=site,
            )
            .distinct()
            .order_by("name")
        )

        mesthiri = (
            Mesthiri.objects
            .filter(
                user=request.user,
                is_active=True,
                entries__site=site,
            )
            .distinct()
            .order_by("name")
        )

        labour_data = []

        for person in labour:

            earned = (
                LabourEntry.objects
                .filter(
                    site=site,
                    labour=person,
                )
                .aggregate(
                    total=Sum("wage")
                )["total"]
                or Decimal("0")
            )

            paid = (
                LabourPayment.objects
                .filter(
                    site=site,
                    labour=person,
                )
                .aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0")
            )

            labour_data.append({
                "id": person.id,
                "name": person.name,
                "worked_days": LabourEntry.objects.filter(
                    site=site,
                    labour=person,
                ).count(),
                "total_earned": str(earned),
                "total_paid": str(paid),
                "total_due": str(
                    earned - paid
                ),
            })

        mesthiri_data = []

        for person in mesthiri:

            earned = (
                MesthiriEntry.objects
                .filter(
                    site=site,
                    mesthiri=person,
                )
                .aggregate(
                    total=Sum("wage")
                )["total"]
                or Decimal("0")
            )

            paid = (
                MesthiriPayment.objects
                .filter(
                    site=site,
                    mesthiri=person,
                )
                .aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0")
            )

            mesthiri_data.append({
                "id": person.id,
                "name": person.name,
                "worked_days": MesthiriEntry.objects.filter(
                    site=site,
                    mesthiri=person,
                ).count(),
                "total_earned": str(earned),
                "total_paid": str(paid),
                "total_due": str(
                    earned - paid
                ),
            })

        total_earned = (
            sum(
                Decimal(x["total_earned"])
                for x in labour_data
            )
            +
            sum(
                Decimal(x["total_earned"])
                for x in mesthiri_data
            )
        )

        total_paid = (
            sum(
                Decimal(x["total_paid"])
                for x in labour_data
            )
            +
            sum(
                Decimal(x["total_paid"])
                for x in mesthiri_data
            )
        )

        return Response({
            "site": {
                "id": site.id,
                "code": site.code,
                "name": site.name,
            },

            "summary": {
                "total_earned":
                    str(total_earned),

                "total_paid":
                    str(total_paid),

                "total_due":
                    str(
                        total_earned -
                        total_paid
                    ),
            },

            "labour": labour_data,
            "mesthiri": mesthiri_data,
        })