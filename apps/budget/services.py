from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from .models import BudgetPeriod
from apps.core.models import User  # Import the User class directly

def generate_next_budget_period(user):
    latest_budget = BudgetPeriod.objects.filter(user=user).order_by('-end_date').first()
    
    if latest_budget:
        start_date = latest_budget.end_date + timedelta(days=1)
    else:
        # TODO: Set this to a users first pay date
        start_date = date.today()

    # Access the Choices from the User CLASS, not the instance
    if user.budget_type == User.PayFrequency.DAYS:
        end_date = start_date + timedelta(days=user.budget_interval_value - 1)
        
    elif user.budget_type == User.PayFrequency.MONTHLY:
        target_day = user.budget_interval_value
        
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
