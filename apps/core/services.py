import json
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from apps.budget.models import BudgetPeriod, CostAllocation
from apps.cost.models import Cost


def calculate_period_totals(financial_items):
    total_year = sum(item.per_year for item in financial_items)
    total_budget = sum(item.per_budget_period for item in financial_items)
    total_week = sum(item.per_week for item in financial_items)

    return {
        "yearly": total_year,
        "monthly": total_year / 12,
        "per_budget": total_budget,
        "per_week": total_week,
    }


# Type to get either Budgeted costs - or Categories
def get_cost_graph_data(user, cost=None, category=None):
    today = timezone.now().date()
    six_months_ago = today - timedelta(days=183)

    budget_periods = BudgetPeriod.objects.filter(
        user=user, end_date__lte=today, end_date__gte=six_months_ago
    ).order_by("start_date")

    if cost:
        allocations = CostAllocation.objects.filter(
            budget_period__user=user,
            cost__name=cost.name,
            budget_period__in=budget_periods,
        )
    elif category:
        allocations = CostAllocation.objects.filter(
            budget_period__user=user,
            category=category,
            budget_period__in=budget_periods,
        )
        # we also need to work out the allocated amount per category
        related_costs = Cost.objects.filter(
            user=user,
            category=category,
        )
        allocated_per_budget = sum([cost.per_budget_period for cost in related_costs])

    allocation_map = defaultdict(float)
    for allocation in allocations:
        allocation_map[allocation.budget_period_id] += -float(allocation.total_paid)

    dates = []
    amounts = []
    for period in budget_periods:
        dates.append(period.end_date.strftime("%d, %b, %y"))
        allocation = allocation_map.get(period.id)
        amounts.append(float(allocation_map.get(period.id, 0.0)))

    if sum(amounts) == 0:
        return None

    average_per_budget = sum(amounts) / len(amounts)

    dates, amounts = pad_graph_data_to_window(
        dates, amounts, budget_periods, six_months_ago
    )

    if cost:
        return {
            "title": cost.name,
            "chart_id": cost.name.lower().replace(" ", ""),
            "dates": json.dumps(dates),
            "amounts": json.dumps(amounts),
            "color": cost.category.color,
            "budgeted_amount": float(cost.amount),
            "average": float(average_per_budget),
        }

    elif category:
        return {
            "title": category.name,
            "chart_id": category.name.lower().replace(" ", ""),
            "dates": json.dumps(dates),
            "amounts": json.dumps(amounts),
            "color": category.color or "#888888",
            "budgeted_amount": allocated_per_budget,
            "average": float(average_per_budget),
        }


def pad_graph_data_to_window(dates, amounts, budget_periods, window_start):
    """
    Prepends zero-value entries to dates/amounts for any gap between
    window_start and the earliest existing budget period.
    """
    if not budget_periods.exists():
        return dates, amounts

    if budget_periods.count() >= 2:
        period_list = list(budget_periods)
        period_length = (period_list[1].start_date - period_list[0].start_date).days
    else:
        period_length = (
            budget_periods.first().end_date - budget_periods.first().start_date
        ).days + 1

    pad_date = budget_periods.first().start_date - timedelta(days=period_length)
    while pad_date >= window_start:
        dates.insert(0, pad_date.strftime("%d %b %y"))
        amounts.insert(0, 0.0)
        pad_date -= timedelta(days=period_length)

    return dates, amounts
