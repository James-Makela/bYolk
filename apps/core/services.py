import json
from collections import defaultdict
from datetime import timedelta

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
        # we also need to work out the allocated amount per category
        related_costs = Cost.objects.filter(
            user=user,
            category=category,
        )
        allocated_per_budget = sum(
            [cost.cost_per_budget_period for cost in related_costs]
        )

    allocation_map = defaultdict(float)
    for allocation in allocations:
        allocation_map[allocation.budget_period_id] += float(abs(allocation.total_paid))

    dates = []
    amounts = []
    for period in budget_periods:
        dates.append(period.start_date.strftime("%d, %b, %y"))
        allocation = allocation_map.get(period.id)
        print(allocation)
        amounts.append(float(allocation_map.get(period.id, 0.0)))

    if sum(amounts) == 0:
        return None

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
            "color": category.color or "#888888",
            "budgeted_amount": allocated_per_budget,
            "average": float(average_per_budget),
        }
