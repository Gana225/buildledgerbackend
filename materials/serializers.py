from decimal import Decimal

from rest_framework import serializers

from .models import Material


class MaterialSerializer(serializers.ModelSerializer):

    class Meta:
        model = Material

        fields = [
            "id",
            "site",
            "serial_number",
            "name",
            "quantity",
            "unit",
            "price",
            "purchase_date",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "site",
            "serial_number",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):

        quantity = attrs.get(
            "quantity",
            getattr(self.instance, "quantity", None),
        )

        price = attrs.get(
            "price",
            getattr(self.instance, "price", None),
        )

        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({
                "quantity": "Quantity must be greater than zero."
            })

        if price is not None and price < 0:
            raise serializers.ValidationError({
                "price": "Price cannot be negative."
            })

        return attrs