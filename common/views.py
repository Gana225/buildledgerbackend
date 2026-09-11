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