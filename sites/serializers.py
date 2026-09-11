from rest_framework import serializers

from .models import Site


class SiteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Site

        fields = [
            "id",
            "code",
            "name",
            "location",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "code",
            "created_at",
            "updated_at",
        ]