from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from sites.models import Site

from .models import Material
from .serializers import MaterialSerializer


class MaterialListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        site_id = self.kwargs["site_id"]

        return Material.objects.filter(
            site_id=site_id,
            site__user=self.request.user,
        )

    def perform_create(self, serializer):

        site_id = self.kwargs["site_id"]

        site = Site.objects.filter(
            id=site_id,
            user=self.request.user,
        ).first()

        if site is None:
            raise ValidationError({
                "site": "Invalid site."
            })

        serializer.save(site=site)


class MaterialDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Material.objects.filter(
            site__user=self.request.user,
        )