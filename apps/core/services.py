from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from functools import singledispatch
from typing import Any

from django.db.models import DecimalField, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone

from apps.budget.models import BudgetPeriod, CostAllocation, IncomeAllocation
from apps.core.constants import ZERO
from apps.core.models import Category, FinancialItem, User
from apps.cost.models import Cost
from apps.income.models import Income


def initialise_session_preferences(request: HttpRequest) -> HttpResponse:
    if not request.session.get("theme"):
        request.session["theme"] = "dark"

    if not request.session.get("privacy_mode"):
        request.session["privacy_mode"] = False

    if not request.session.get("graph_period"):
        request.session["graph_period"] = 365

    return redirect(request.META.get("HTTP_REFERER", "/"))


def calculate_period_totals(
    financial_items: QuerySet[FinancialItem],
) -> dict[str, Decimal]:
    total_year = sum(item.per_year for item in financial_items)
    total_budget = sum(item.per_budget_period for item in financial_items)
    total_week = sum(item.per_week for item in financial_items)

    return {
        "yearly": Decimal(total_year),
        "monthly": Decimal(total_year / 12),
        "per_budget": Decimal(total_budget),
        "per_week": Decimal(total_week),
    }


def get_budget_periods(
    user: User, time_period: int = 365
) -> tuple[list[BudgetPeriod], date]:
    today = timezone.now().date()
    past_date = today - timedelta(days=time_period)

    budget_periods: QuerySet[BudgetPeriod] = BudgetPeriod.objects.filter(
        user=user, start_date__lte=today, start_date__gte=past_date
    ).order_by("start_date")

    return list(budget_periods), past_date


def get_total_spend_data(user: User, time_period: int = 365) -> list[float] | None:
    budget_periods, past_date = get_budget_periods(user, time_period)

    allocations: QuerySet[CostAllocation] = CostAllocation.objects.filter(
        budget_period__user=user,
        budget_period__in=budget_periods,
    ).annotate(total_paid_amount=Coalesce(Sum("transactions__amount"), ZERO))

    allocation_map: dict[float, float] = defaultdict(float)
    for allocation in allocations:
        allocation_map[allocation.budget_period_id] += float(
            getattr(allocation, "total_paid_amount", ZERO)
        )

    amounts = []
    for period in budget_periods:
        amounts.append(float(allocation_map.get(period.id, 0.0)))

    if sum(amounts) == 0:
        return None

    _, amounts = _pad_graph_data_to_window(amounts, budget_periods, past_date)

    return amounts


# Type to get either Budgeted costs - or Categories
@singledispatch
def get_graph_data(
    entity: Income | Cost | Category, user: User, time_period: int
) -> dict[str, Any] | None:
    raise NotImplementedError(f"unsupported target type: {type(entity)}")


# INCOME GRAPH DATA
@get_graph_data.register
def _(entity: Income, user: User, time_period: int = 365) -> dict[str, Any] | None:
    income = entity
    budget_periods, past_date = get_budget_periods(user, time_period)

    allocations: QuerySet[IncomeAllocation] = IncomeAllocation.objects.filter(
        budget_period__user=user,
        income__name=income.name,
        budget_period__in=budget_periods,
    ).annotate(total_paid_amount=Coalesce(Sum("transactions__amount"), ZERO))

    _, padded_dates, amounts = _map_allocations(allocations, budget_periods, past_date)

    return {
        "title": income.name,
        "dates": padded_dates,
        "amounts": amounts,
    }


# COST GRAPH DATA
@get_graph_data.register
def _(entity: Cost, user: User, time_period: int = 365) -> dict[str, Any] | None:
    cost = entity
    budget_periods, past_date = get_budget_periods(user, time_period)

    allocations: QuerySet[CostAllocation] = CostAllocation.objects.filter(
        budget_period__user=user,
        cost__name=entity.name,
        budget_period__in=budget_periods,
    ).annotate(total_paid_amount=Coalesce(Sum("transactions__amount"), ZERO))

    average_per_budget, padded_dates, amounts = _map_allocations(
        allocations, budget_periods, past_date
    )

    if sum(amounts) == 0:
        return None

    return {
        "title": cost.name,
        "chart_id": cost.name.lower().replace(" ", ""),
        "dates": padded_dates,
        "amounts": amounts,
        "color": cost.category.color if cost.category else None,
        "average": average_per_budget,
        "budgeted_amount": float(cost.amount),
    }


# CATEGORY GRAPH DATA
@get_graph_data.register
def _(entity: Category, user: User, time_period: int = 365) -> dict[str, Any] | None:
    category = entity
    budget_periods, past_date = get_budget_periods(user, time_period)

    allocations: QuerySet[CostAllocation] = CostAllocation.objects.filter(
        budget_period__user=user,
        category=category,
        budget_period__in=budget_periods,
    ).annotate(
        total_paid_amount=Coalesce(
            Sum("transactions__amount"), Value(0, output_field=DecimalField())
        )
    )

    # we also need to work out the allocated amount per category
    related_costs: QuerySet[Cost] = Cost.objects.filter(
        user=user,
        category=category,
    )
    allocated_per_budget = sum(cost.per_budget_period for cost in related_costs)

    average_per_budget, padded_dates, amounts = _map_allocations(
        allocations, budget_periods, past_date
    )

    if sum(amounts) == 0:
        return None

    return {
        "title": category.name,
        "chart_id": category.name.lower().replace(" ", ""),
        "dates": padded_dates,
        "amounts": amounts,
        "color": category.color or "#888888",
        "average": average_per_budget,
        "budgeted_amount": float(allocated_per_budget),
    }


def _map_allocations(
    allocations: QuerySet[CostAllocation | IncomeAllocation],
    budget_periods: list[BudgetPeriod],
    past_date: date,
) -> tuple[float, list[date] | None, list[float]]:
    print(allocations)
    is_income = type(allocations) is QuerySet[IncomeAllocation]

    allocation_map: dict[float, float] = defaultdict(float)
    for allocation in allocations:
        if is_income:
            allocation_map[allocation.budget_period_id] += float(
                getattr(allocation, "total_paid_amount")
            )
        else:
            allocation_map[allocation.budget_period_id] += -float(
                getattr(allocation, "total_paid_amount")
            )

    dates = []
    amounts = []
    for period in budget_periods:
        dates.append(period.end_date)
        amounts.append(float(allocation_map.get(period.id, 0.0)))

    if not amounts:
        return 0.0, [], []
    if sum(amounts) == 0 and not is_income:
        return 0.0, [], []

    average_per_budget = sum(amounts) / len(amounts)

    padded_dates, amounts = _pad_graph_data_to_window(
        amounts, budget_periods, past_date, dates
    )

    return average_per_budget, padded_dates, amounts


def _pad_graph_data_to_window(
    amounts: list[float],
    budget_periods: list[BudgetPeriod],
    window_start: date,
    dates: list[date] | None = None,
) -> tuple[list[date] | None, list[float]]:
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
