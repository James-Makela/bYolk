from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from .models import BudgetPeriod, CostAllocation
from apps.core.models import User, FrequencyUnit
from apps.cost.models import Cost

def generate_next_budget_period(user):
    latest_budget = BudgetPeriod.objects.filter(user=user).order_by('-end_date').first()
    
    if latest_budget:
        start_date = latest_budget.end_date + timedelta(days=1)
    else:
        # TODO: Set this to a users first pay date
        start_date = date.today()

    # Access the Choices from the User CLASS, not the instance
    if user.budget_type == FrequencyUnit.DAY:
        end_date = start_date + timedelta(days=user.budget_interval - 1)
        
    elif user.budget_type == FrequencyUnit.MONTH:
        target_day = user.budget_interval
        
        next_month_date = start_date + relativedelta(months=1)
        try:
            end_of_next_period_start = next_month_date.replace(day=target_day)
        except ValueError:
            # relativedelta(day=31) handles the "last day of month" logic for us
            end_of_next_period_start = next_month_date + relativedelta(day=31)

        end_date = end_of_next_period_start - timedelta(days=1)

    return BudgetPeriod.objects.create(
        user=user,
        start_date=start_date,
        end_date=end_date,
    )

def populate_from_costs(budget_period, user):
    costs = Cost.objects.filter(user=user)
    cost_allocations_to_create = []
    for cost in costs:
        print(cost)
        print(f"User budget type: {user.budget_type}, Cost type: {cost.frequency_unit}")
        print(f"User budget interval: {user.budget_interval}, Cost interval: {cost.frequency_value}")
        if cost.frequency_value == user.budget_interval and cost.frequency_unit == user.budget_type:
            cost_allocations_to_create.append(CostAllocation(
                user=user,
                budget_period=budget_period,
                cost=cost,
                cost_name=cost.name,
                cost_amount=cost.amount,
            ))
    return CostAllocation.objects.bulk_create(
        cost_allocations_to_create,
        ignore_conflicts=True
    )

