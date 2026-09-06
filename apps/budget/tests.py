from decimal import Decimal

from django.contrib.auth import get_user_model

from apps.core.tests import FinancialTestBase

from .models import BudgetPeriod, CostAllocation
from .services import generate_next_budget_period, populate_from_costs

# from django.test import TestCase


User = get_user_model()


class BudgetPeriodTests(FinancialTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        generate_next_budget_period(cls.user)
        generate_next_budget_period(cls.user)

        cls.budget_periods = BudgetPeriod.objects.filter(user=cls.user)

    def test_budget_period_sting_method(self):
        self.assertEqual(
            str(self.budget_periods[0]), "Budget 1 2026-01-01 -> 2026-01-14"
        )

    def test_budget_period_populates_from_costs(self):
        for budget_period in self.budget_periods:
            populate_from_costs(budget_period, self.user)

        allocations = CostAllocation.objects.filter(
            budget_period=self.budget_periods[0]
        )

        self.assertEqual(len(allocations), 3)

    def test_budget_period_properties(self):
        budget = self.budget_periods[0]
        populate_from_costs(budget, self.user)

        self.assertEqual(budget.get_total_costs, Decimal(-930.00))
        self.assertEqual(budget.get_original_costs, Decimal(-930.00))
        self.assertEqual(budget.get_total_income, Decimal(3000.00))
        self.assertEqual(budget.theoretical_balance, Decimal(2070.00))
        self.assertEqual(budget.balance, Decimal(2070.00))
