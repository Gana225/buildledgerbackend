from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from materials.models import Material
from sites.models import Site


User = get_user_model()


class MaterialTests(APITestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            username="material_user_a",
            email="materiala@example.com",
            password="TestPassword123!",
        )

        self.user_b = User.objects.create_user(
            username="material_user_b",
            email="materialb@example.com",
            password="TestPassword123!",
        )

        self.site_a = Site.objects.create(
            user=self.user_a,
            name="User A Site",
        )

        self.site_b = Site.objects.create(
            user=self.user_b,
            name="User B Site",
        )

        self.material_a = Material.objects.create(
            site=self.site_a,
            name="Cement",
            quantity="10.00",
            unit="bags",
            price="5000.00",
            purchase_date="2026-09-10",
        )

        self.material_b = Material.objects.create(
            site=self.site_b,
            name="Steel",
            quantity="100.00",
            unit="kg",
            price="10000.00",
            purchase_date="2026-09-10",
        )

        self.client.force_authenticate(
            user=self.user_a
        )

        self.material_list_url = reverse(
            "material-list-create",
            kwargs={
                "site_id": self.site_a.id
            },
        )

    def test_user_can_create_material(self):
        response = self.client.post(
            self.material_list_url,
            {
                "name": "Sand",
                "quantity": "20.00",
                "unit": "bags",
                "price": "3000.00",
                "purchase_date": "2026-09-10",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Material.objects.filter(
                site=self.site_a,
                name="Sand",
            ).exists()
        )

    def test_user_only_sees_own_site_materials(self):
        response = self.client.get(
            self.material_list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        returned_ids = [
            item["id"]
            for item in response.data
        ]

        self.assertIn(
            self.material_a.id,
            returned_ids,
        )

        self.assertNotIn(
            self.material_b.id,
            returned_ids,
        )

    def test_user_cannot_see_another_users_site_materials(self):
        url = reverse(
            "material-list-create",
            kwargs={
                "site_id": self.site_b.id
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data,
            [],
        )

    def test_user_cannot_create_material_for_another_users_site(self):
        url = reverse(
            "material-list-create",
            kwargs={
                "site_id": self.site_b.id
            },
        )

        response = self.client.post(
            url,
            {
                "name": "Unauthorized Cement",
                "quantity": "10.00",
                "unit": "bags",
                "price": "5000.00",
                "purchase_date": "2026-09-10",
            },
            format="json",
        )

        self.assertNotEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertFalse(
            Material.objects.filter(
                site=self.site_b,
                name="Unauthorized Cement",
            ).exists()
        )

    def test_zero_quantity_is_rejected(self):
        response = self.client.post(
            self.material_list_url,
            {
                "name": "Sand",
                "quantity": "0",
                "unit": "bags",
                "price": "3000.00",
                "purchase_date": "2026-09-10",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_negative_quantity_is_rejected(self):
        response = self.client.post(
            self.material_list_url,
            {
                "name": "Sand",
                "quantity": "-10",
                "unit": "bags",
                "price": "3000.00",
                "purchase_date": "2026-09-10",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_negative_price_is_rejected(self):
        response = self.client.post(
            self.material_list_url,
            {
                "name": "Sand",
                "quantity": "20.00",
                "unit": "bags",
                "price": "-3000.00",
                "purchase_date": "2026-09-10",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_serial_number_is_generated(self):
        response = self.client.post(
            self.material_list_url,
            {
                "name": "Bricks",
                "quantity": "1000.00",
                "unit": "pieces",
                "price": "8000.00",
                "purchase_date": "2026-09-10",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["serial_number"],
            2,
        )

    def test_serial_numbers_are_unique_per_site(self):
        material = Material.objects.create(
            site=self.site_a,
            serial_number=50,
            name="Test Material",
            quantity="10.00",
            unit="bags",
            price="1000.00",
            purchase_date="2026-09-10",
        )

        self.assertIsNotNone(
            material.id
        )

        with self.assertRaises(Exception):
            Material.objects.create(
                site=self.site_a,
                serial_number=50,
                name="Duplicate Material",
                quantity="5.00",
                unit="bags",
                price="500.00",
                purchase_date="2026-09-10",
            )