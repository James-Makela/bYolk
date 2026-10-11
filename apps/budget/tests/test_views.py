from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.core.tests import FinancialTestBase
from apps.core.models import Category, UserPreferences

from ..models import BudgetPeriod, CostAllocation
from ..forms import CostAllocationForm

from ..services import generate_next_budget_period, populate_from_costs

User = get_user_model()


class BudgetAddSingleAllocationViewTests(FinancialTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        generate_next_budget_period(cls.user)
        cls.budget_period = BudgetPeriod.objects.filter(user=cls.user).first()
        cls.category = Category.objects.create(user=cls.user, name="Transport")

        cls.other_user = User.objects.create_user(
            email="other@example.com", password="testpass123"
        )
        cls.preferences = UserPreferences.objects.create(
            user=cls.other_user,
            frequency_value=2,
            frequency_unit="weeks",
            first_budget_date=datetime(2026, 1, 1),
        )
        generate_next_budget_period(user=cls.other_user)
        cls.other_period = BudgetPeriod.objects.filter(user=cls.other_user).first()
        cls.other_category = Category.objects.create(user=cls.other_user, name="Computer Parts")

        cls.url = reverse("add-cost-allocation", args=[cls.budget_period.id])
        cls.detail_url = reverse("detail", args=[cls.budget_period.id])

    def setUp(self):
        self.client.force_login(self.user)

    # Access Control
    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_unable_to_access_other_user_budget(self):
        url = reverse("add-cost-allocation", args=[self.other_period.id])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {}).status_code, 404)

    def test_non_existent_budget_returns_404(self):
        url = reverse("add-cost-allocation", args=[247])
        self.assertEqual(self.client.get(url).status_code, 404)

    # Get behaviour
    def test_get_renders_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "budget/forms/add_allocation_form.html")
        self.assertIsInstance(response.context["form"], CostAllocationForm)
        self.assertEqual(response.context["budget_id"], self.budget_period.id)

    def test_can_only_get_own_categories(self):

        response = self.client.get(self.url)
        form_categories = response.context["form"].fields['category'].queryset

        self.assertNotIn(self.other_category, form_categories)
        self.assertIn(self.category, form_categories)

    # Post behaviour
    def test_creates_one_off_allocation_with_valid_data(self):
        data = {
            "name": "Car Mechanic",
            "category": self.category.pk,
            "amount": 50.00,
        }
        response = self.client.post(self.url, data)
        messages = [str(message) for message in get_messages(response.wsgi_request)]

        self.assertRedirects(response, self.detail_url, fetch_redirect_response=False)
        allocation = CostAllocation.objects.get()
        self.assertEqual(allocation.name, "Car Mechanic")
        self.assertEqual(allocation.amount, Decimal(-50.00))
        self.assertEqual(allocation.category, self.category)
        self.assertEqual(messages, ["Allocation added!"])

    def test_invalid_post_fails(self):
        data = {
            "name": "New CPU",
            "category": self.other_category.pk,
            "amount": 350.00,
        }
        response = self.client.post(self.url, data)
        messages = [str(message) for message in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertEqual(f"/budgets/{self.budget_period.id}/", response.url)
        self.assertEqual(messages, ["Unable to save allocation."])
