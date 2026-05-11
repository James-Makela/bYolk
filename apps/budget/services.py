from datetime import date, timedelta

from apps.budget.models import BudgetPeriod, CostAllocation, IncomeAllocation
from apps.cost.models import Cost
from apps.income.models import Income


def generate_next_budget_period(user):
    # Get the latest budget period
    latest_budget = BudgetPeriod.objects.filter(user=user).order_by("-end_date").first()

    # Determine the start date
    if latest_budget:
        start_date = latest_budget.end_date + timedelta(days=1)
    else:
        start_date = getattr(user.preferences, "first_budget_date", date.today())

    delta = user.preferences.get_delta()

    end_date = (start_date + delta) - timedelta(days=1)

    return BudgetPeriod.objects.create(
        user=user,
        start_date=start_date,
        end_date=end_date,
    )


def populate_from_costs(budget_period, user):
    costs = Cost.objects.filter(user=user)
    incomes = Income.objects.filter(user=user)
    cost_data = []
    income_data = []

    for cost in costs:
        delta = cost.get_delta()
        current_occurrence = cost.start_date

        while current_occurrence <= budget_period.end_date:
            if current_occurrence >= budget_period.start_date:
                cost_data.append(
                    CostAllocation(
                        budget_period=budget_period,
                        cost=cost,
                        name=cost.name,
                        amount=cost.amount,
                        expected_date=current_occurrence,
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
                        expected_date=current_occurrence,
                    )
                )

            current_occurrence += delta
            if not any([delta.years, delta.months, delta.weeks, delta.days]):
                break

    cost_allocations = CostAllocation.objects.bulk_create(
        cost_data, ignore_conflicts=True
    )
    income_allocations = IncomeAllocation.objects.bulk_create(
        income_data, ignore_conflicts=True
    )

    return {
        "cost": cost_allocations,
        "income": income_allocations,
    }
