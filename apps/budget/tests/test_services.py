from datetime import date

from apps.core.tests import FinancialTestBase

from ..models import BudgetPeriod, CostAllocation
from ..services import generate_next_budget_period, populate_from_costs


class BudgetServiceTests(FinancialTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        generate_next_budget_period(cls.user)
        generate_next_budget_period(cls.user)

        cls.budget_periods = BudgetPeriod.objects.filter(user=cls.user)

    def test_generate_next_budget_period(self):
        generated_budget = generate_next_budget_period(self.user)
        self.assertIsInstance(generated_budget, BudgetPeriod)
        self.assertEqual(generated_budget.start_date, date.fromisoformat("2026-01-29"))
        self.assertEqual(generated_budget.user, self.user)

    def test_budget_period_populates_from_costs(self):
        for budget_period in self.budget_periods:
            populate_from_costs(budget_period)

        allocations = CostAllocation.objects.filter(
            budget_period=self.budget_periods[0]
        )

        self.assertEqual(len(allocations), 3)
