# from rest_framework import generics
# from rest_framework.permissions import IsAuthenticated
# from django.shortcuts import get_object_or_404

# from .models import Labour, LabourEntry
# from .serializers import (
#     LabourSerializer,
#     LabourEntrySerializer,
# )


# class LabourListCreateView(generics.ListCreateAPIView):

#     serializer_class = LabourSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         site_id = self.kwargs["site_id"]

#         return Labour.objects.filter(
#             site_id=site_id,
#             site__user=self.request.user,
#         )

#     def perform_create(self, serializer):
#         site_id = self.kwargs["site_id"]

#         from sites.models import Site

#         site = get_object_or_404(
#             Site.objects.filter(
#                 id=site_id,
#                 user=self.request.user,
#             )
#         )

#         serializer.save(site=site)


# class LabourDetailView(generics.RetrieveUpdateDestroyAPIView):

#     serializer_class = LabourSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Labour.objects.filter(
#             site__user=self.request.user,
#         )


# class LabourEntryListCreateView(
#     generics.ListCreateAPIView
# ):

#     serializer_class = LabourEntrySerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         site_id = self.kwargs["site_id"]

#         return LabourEntry.objects.filter(
#             labour__site_id=site_id,
#             labour__site__user=self.request.user,
#         )

#     def perform_create(self, serializer):
#         site_id = self.kwargs["site_id"]

#         labour_id = self.request.data.get("labour")

#         labour = Labour.objects.filter(
#             id=labour_id,
#             site_id=site_id,
#             site__user=self.request.user,
#         ).first()

#         if labour is None:
#             from rest_framework.exceptions import ValidationError

#             raise ValidationError({
#                 "labour": "Invalid labour for this site."
#             })

#         serializer.save(labour=labour)


# class LabourEntryDetailView(
#     generics.RetrieveUpdateDestroyAPIView
# ):

#     serializer_class = LabourEntrySerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return LabourEntry.objects.filter(
#             labour__site__user=self.request.user,
#         )



from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sites.models import Site

from .models import (
    Labour,
    LabourAssignment,
    LabourEntry,
)

from .serializers import (
    LabourSerializer,
    LabourAssignmentSerializer,
    LabourEntrySerializer,
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