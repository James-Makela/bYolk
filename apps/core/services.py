from collections import defaultdict
from datetime import timedelta

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.budget.models import BudgetPeriod, CostAllocation, IncomeAllocation
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


def get_budget_periods(user, time_period=365):
    today = timezone.now().date()
    past_date = today - timedelta(days=time_period)

    budget_periods = BudgetPeriod.objects.filter(
        user=user, start_date__lte=today, start_date__gte=past_date
    ).order_by("start_date")

    return list(budget_periods), past_date


def get_total_spend_data(user, time_period=365):
    budget_periods, past_date = get_budget_periods(user, time_period)

    allocations = CostAllocation.objects.filter(
        budget_period__user=user,
        budget_period__in=budget_periods,
    ).annotate(
        total_paid_amount=Coalesce(
            Sum("transactions__amount"), Value(0, output_field=DecimalField())
        )
    )

    allocation_map = defaultdict(float)
    for allocation in allocations:
        allocation_map[allocation.budget_period_id] += float(
            allocation.total_paid_amount
        )

    amounts = []
    for period in budget_periods:
        amounts.append(float(allocation_map.get(period.id, 0.0)))

    if sum(amounts) == 0:
        return None

    _, amounts = pad_graph_data_to_window(amounts, budget_periods, past_date)

    return amounts


# Type to get either Budgeted costs - or Categories
def get_graph_data(user, cost=None, income=None, category=None, time_period=365):
    budget_periods, past_date = get_budget_periods(user, time_period)

    if cost:
        allocations = CostAllocation.objects.filter(
            budget_period__user=user,
            cost__name=cost.name,
            budget_period__in=budget_periods,
        )
    elif income:
        allocations = IncomeAllocation.objects.filter(
            budget_period__user=user,
            income__name=income.name,
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
        allocated_per_budget = sum(cost.per_budget_period for cost in related_costs)
    else:
        raise ValueError("get_graph_data requires a cost, income, or category")

    allocations = allocations.annotate(
        total_paid_amount=Coalesce(
            Sum("transactions__amount"), Value(0, output_field=DecimalField())
        )
    )

    allocation_map = defaultdict(float)
    for allocation in allocations:
        if income:
            allocation_map[allocation.budget_period_id] += float(
                allocation.total_paid_amount
            )
        else:
            allocation_map[allocation.budget_period_id] += -float(
                allocation.total_paid_amount
            )

    dates = []
    amounts = []
    for period in budget_periods:
        dates.append(period.end_date)
        amounts.append(float(allocation_map.get(period.id, 0.0)))

    if not amounts:
        return None
    if sum(amounts) == 0 and not income:
        return None

    average_per_budget = sum(amounts) / len(amounts)

    dates, amounts = pad_graph_data_to_window(amounts, budget_periods, past_date, dates)

    if cost:
        return {
            "title": cost.name,
            "chart_id": cost.name.lower().replace(" ", ""),
            "dates": dates,
            "amounts": amounts,
            "color": cost.category.color,
            "budgeted_amount": float(cost.amount),
            "average": float(average_per_budget),
        }

    elif income:
        return {
            "title": income.name,
            "dates": dates,
            "amounts": amounts,
        }

    elif category:
        return {
            "title": category.name,
            "chart_id": category.name.lower().replace(" ", ""),
            "dates": dates,
            "amounts": amounts,
            "color": category.color or "#888888",
            "budgeted_amount": float(allocated_per_budget),
            "average": float(average_per_budget),
        }


def pad_graph_data_to_window(amounts, budget_periods, window_start, dates=None):
    """
    Prepends zero-value entries to dates/amounts for any gap between
    window_start and the earliest existing budget period.
    """
    if not budget_periods:
        return dates, amounts

    if len(budget_periods) >= 2:
        period_length = (
            budget_periods[1].start_date - budget_periods[0].start_date
        ).days
    else:
        period_length = (
            budget_periods[0].end_date - budget_periods[0].start_date
        ).days + 1

    pad_date = budget_periods[0].start_date - timedelta(days=period_length)
    while pad_date >= window_start:
        if dates:
            dates.insert(0, pad_date)
        amounts.insert(0, 0.0)
        pad_date -= timedelta(days=period_length)

    return dates, amounts
