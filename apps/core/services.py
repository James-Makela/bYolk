import json
from datetime import date, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.budget.models import BudgetPeriod, CostAllocation
from apps.cost.models import Cost


# Type to get either Budgeted costs - or Categories
def get_cost_graph_data(user, cost=None, category=None):
    today = timezone.now().date()

    budget_periods = BudgetPeriod.objects.filter(
        user=user,
        end_date__lte=today,
        end_date__gte=today - timedelta(days=183),
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

    allocation_map = {a.budget_period_id: a for a in allocations}

    dates = []
    amounts = []
    for period in budget_periods:
        dates.append(period.start_date.strftime("%d, %b, %Y"))
        allocation = allocation_map.get(period.id)
        amounts.append(float(abs(allocation.total_paid)) if allocation else 0.0)

    average_per_budget = sum(amounts) / len(amounts)

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
            "color": category.color,
            "budgeted_amount": 0,
            "average": float(average_per_budget),
        }
