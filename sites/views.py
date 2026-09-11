from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Site
from .serializers import SiteSerializer


class SiteListCreateView(generics.ListCreateAPIView):

    serializer_class = SiteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Site.objects.filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user
        )


class SiteDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = SiteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Site.objects.filter(
            user=self.request.user
        )