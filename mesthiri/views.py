from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sites.models import Site
from .models import Mesthiri, MesthiriAssignment, MesthiriEntry
from .serializers import MesthiriAssignmentSerializer, MesthiriEntrySerializer, MesthiriSerializer


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
