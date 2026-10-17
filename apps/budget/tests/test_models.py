from decimal import Decimal

from apps.core.tests import FinancialTestBase

from ..models import BudgetPeriod
from ..services import generate_next_budget_period, populate_from_costs


class BudgetPeriodTests(FinancialTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        generate_next_budget_period(cls.user)
        generate_next_budget_period(cls.user)

        cls.budget_periods = BudgetPeriod.objects.filter(user=cls.user)

    def test_budget_period_string_method(self):

        budget_period = self.budget_periods[0]
        self.assertEqual(
            str(budget_period), f"Budget {budget_period.id} 2026-01-01 -> 2026-01-14"
        )

    def test_budget_period_properties(self):
        budget = self.budget_periods[0]
        populate_from_costs(budget)

        self.assertEqual(budget.get_total_costs, Decimal(-930.00))
        self.assertEqual(budget.get_original_costs, Decimal(-930.00))
        self.assertEqual(budget.get_total_income, Decimal(3000.00))
        self.assertEqual(budget.theoretical_balance, Decimal(2070.00))
        self.assertEqual(budget.balance, Decimal(2070.00))
