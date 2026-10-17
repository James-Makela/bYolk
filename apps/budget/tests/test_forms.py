from apps.core.models import Category
from apps.core.tests import FinancialTestBase

from ..forms import CostAllocationForm
from ..models import BudgetPeriod
from ..services import generate_next_budget_period


class BudgetPeriodFormTests(FinancialTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        generate_next_budget_period(cls.user)
        generate_next_budget_period(cls.user)
        cls.budget_periods = BudgetPeriod.objects.filter(user=cls.user)
        cls.category_transport = Category.objects.create(
            user=cls.user, name="Transport"
        )
        cls.category_food = Category.objects.create(user=cls.user, name="Food")

    def test_instantiate_form(self):
        form = CostAllocationForm(user=self.user)
        form_categories = form.fields["category"].queryset

        self.assertIn(self.category_transport, form_categories)
