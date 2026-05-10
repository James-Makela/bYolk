from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.models import Category

from .models import Cost

User = get_user_model()


class CostTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="test", email="test@test.com", password="testpass123"
        )
        Category.objects.create(user=cls.user, name="Housing")

    def test_create_cost(self):
        cost = Cost.objects.create(
            frequency_value=1,
            frequency_unit="weeks",
            user=self.user,
            name="Rent",
            amount=400,
            category=Category.objects.get(
                user=self.user,
                name="Housing",
            ),
            start_date=datetime(2026, 1, 6),
        )

        self.assertIsInstance(cost, Cost)
        self.assertEqual(cost.name, "Rent")
        self.assertEqual(cost.frequency_string(), "Every Week")
        self.assertEqual(cost.user, self.user)
        self.assertEqual(cost.amount, 400)
        self.assertEqual(cost.category.name, "Housing")
        self.assertEqual(cost.start_date, datetime(2026, 1, 6))
