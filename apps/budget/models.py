from django.db import models
from apps.core.models import User
from apps.cost.models import Cost


class BudgetPeriod(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'
        PENDING = 'pending', 'Pending'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    notes = models.CharField(max_length=250, blank=True)

    def __str__(self):
        return f"Budget {self.id} {self.start_date} -> {self.end_date}"


class CostAllocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    budget_period = models.ForeignKey(
        BudgetPeriod,
        on_delete=models.CASCADE
    )
    cost = models.ForeignKey(
        Cost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    cost_name = models.CharField(max_length=50)
    cost_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["budget_period", "cost"],
                name="unique_cost_per_budget")
        ]


    def save(self, *args, **kwargs):
        if self.cost and not self.cost_name:
            self.cost_name = self.cost.name
            self.cost_amount = self.cost.amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cost_name} ${self.cost_amount} for Budget {self.budget_period_id}"
