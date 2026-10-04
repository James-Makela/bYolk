from decimal import Decimal

from django.utils import timezone

from apps.core.models import User
from apps.cost.models import Cost, CostChange


def save_cost(
    cost: Cost | None,
    old_amount: Decimal | None,
    field_values: dict[str, Decimal],
    user: User,
    log_change: bool,
) -> Cost:
    """
    Creates or updates a Cost object and returns the new cost for any required
    updates to future cost allocations.
    """
    new_amount = field_values["amount"]

    cost = cost or Cost()
    cost.user = user
    # Assumes there are no additional fields that are not in the Cost model
    for field, value in field_values.items():
        setattr(cost, field, value)
    cost.save()

    _sync_change_log(cost, old_amount, new_amount, log_change)
    return cost


def _sync_change_log(
    cost: Cost, old_amount: Decimal | None, new_amount: Decimal, log_change: bool
) -> None:
    today = timezone.now().date()
    existing_change: CostChange | None = CostChange.objects.filter(
        cost=cost, date_changed=today
    ).first()

    baseline_amount = existing_change.previous_amount if existing_change else old_amount

    if baseline_amount is None or not log_change or baseline_amount == new_amount:
        if existing_change:
            existing_change.delete()
        return
    elif log_change:
        print("Creating cost change")
        CostChange.objects.update_or_create(
            cost=cost,
            date_changed=today,
            defaults={
                "new_amount": new_amount,
            },
            create_defaults={
                "new_amount": new_amount,
                "previous_amount": baseline_amount,
            },
        )
