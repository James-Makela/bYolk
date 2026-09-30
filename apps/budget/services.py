from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import QuerySet, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.assets.models import SavingsAccount
from apps.budget.models import (
    BudgetPeriod,
    CostAllocation,
    IncomeAllocation,
)
from apps.core.constants import ZERO
from apps.core.models import User
from apps.cost.models import Cost
from apps.income.models import Income


def generate_next_budget_period(user: User) -> BudgetPeriod:
    # Get the latest budget period
    latest_budget: BudgetPeriod | None = (
        BudgetPeriod.objects.filter(user=user).order_by("-end_date").first()
    )

    # Determine the start date
    if latest_budget:
        start_date = latest_budget.end_date + timedelta(days=1)
    else:
        start_date = getattr(user.preferences, "first_budget_date", date.today())

    delta = user.preferences.get_delta()

    end_date = (start_date + delta) - timedelta(days=1)

    return BudgetPeriod.objects.create(  # zuban: ignore
        user=user,
        start_date=start_date,
        end_date=end_date,
    )


def populate_from_costs(
    budget_period: BudgetPeriod, user: User
) -> dict[str, list[Any]]:
    costs: QuerySet[Cost] = Cost.objects.filter(user=user)
    incomes: QuerySet[Income] = Income.objects.filter(user=user)
    cost_data = []
    income_data = []

    for cost in costs:
        delta = cost.get_delta()
        current_occurrence: date = cost.start_date

        if cost.end_date and cost.end_date < budget_period.start_date:
            continue

        while current_occurrence <= budget_period.end_date:
            if current_occurrence >= budget_period.start_date:
                if cost.category is not None:
                    category = cost.category
                else:
                    category = None
                cost_data.append(
                    CostAllocation(
                        budget_period=budget_period,
                        cost=cost,
                        name=cost.name,
                        amount=-cost.amount,
                        expected_amount=-cost.amount,
                        expected_date=current_occurrence,
                        category=category,
                    )
                )

            current_occurrence += delta
            if not any([delta.years, delta.months, delta.weeks, delta.days]):
                break

    for income in incomes:
        delta = income.get_delta()
        current_occurrence = income.start_date

        while current_occurrence <= budget_period.end_date:
            if current_occurrence >= budget_period.start_date:
                income_data.append(
                    IncomeAllocation(
                        budget_period=budget_period,
                        income=income,
                        name=income.name,
                        amount=income.amount,
                        expected_amount=income.amount,
                        expected_date=current_occurrence,
                    )
                )

            current_occurrence += delta
            if not any([delta.years, delta.months, delta.weeks, delta.days]):
                break

    cost_allocations: list[CostAllocation] = CostAllocation.objects.bulk_create(
        cost_data, ignore_conflicts=True
    )
    income_allocations: list[IncomeAllocation] = IncomeAllocation.objects.bulk_create(
        income_data, ignore_conflicts=True
    )

    return {
        "cost": cost_allocations,
        "income": income_allocations,
    }


def get_running_savings(
    user: User, viewed_budget_period: BudgetPeriod
) -> tuple[Decimal, Decimal]:
    today = timezone.now().date()

    current_savings: SavingsAccount | None = SavingsAccount.objects.filter(
        user=user, is_primary=True
    ).first()

    if not current_savings:
        return ZERO, ZERO

    predicted_balance = current_savings.value
    theoretical_balance = current_savings.value

    inclusive_periods: QuerySet[BudgetPeriod] = BudgetPeriod.objects.filter(
        user=user,
        end_date__gte=today,
        end_date__lte=viewed_budget_period.end_date,
    ).order_by("start_date")

    for budget_period in inclusive_periods:
        predicted_balance += budget_period.balance
        theoretical_balance += budget_period.theoretical_balance

    return theoretical_balance, predicted_balance


def sync_future_allocations(cost: Cost) -> None:
    """Updates any future allocations when a cost is updated"""
    CostAllocation.objects.filter(
        cost=cost,
        expected_date__gt=timezone.now().date(),
    ).update(
        amount=-cost.amount,
        expected_amount=-cost.amount,
        name=cost.name,
    )


def get_category_pie_context(
    user: User, budget_id: int, forecast: bool = True
) -> dict[str, Any]:
    budget: BudgetPeriod = get_object_or_404(
        BudgetPeriod.objects.filter(
            user=user,
            pk=budget_id,
        )
    )

    if forecast:
        category_totals: QuerySet["CostAllocation", dict[str, Decimal]] = (
            CostAllocation.objects.filter(budget_period=budget)
            .values("category__name", "category__color")
            .annotate(total=Coalesce(Sum("expected_amount"), Decimal(0.0)))
            .order_by("total")
        )
    else:
        category_totals = (
            CostAllocation.objects.filter(budget_period=budget)
            .values("category__name", "category__color")
            .annotate(total=Coalesce(Sum("transactions__amount"), Decimal(0.0)))
            .order_by("total")
            .exclude(total=0)
        )

    pie_category_labels = []
    pie_category_series = []
    pie_category_colors = []

    if len(category_totals) > 0:
        print(category_totals[0])

    if forecast:
        for item in category_totals:
            pie_category_labels.append(item["category__name"] or "Uncategorized")
            pie_category_series.append(abs(float(item["total"])))
            pie_category_colors.append(item["category__color"] or "#999999")
    else:
        for item in category_totals:
            pie_category_labels.append(item["category__name"] or "Uncategorized")
            pie_category_series.append(abs(float(item["total"])))
            pie_category_colors.append(item["category__color"] or "#999999")

    return {
        "pie_category_labels": pie_category_labels,
        "pie_category_series": pie_category_series,
        "pie_category_colors": pie_category_colors,
        "budget": budget,
        "forecast": forecast,
        "next_forecast_value": not forecast,
    }
