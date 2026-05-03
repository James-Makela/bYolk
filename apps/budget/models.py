from django.db import models
from django.db.models import Sum, Q, OuterRef, Subquery, Value, DecimalField
from django.db.models.functions import Coalesce, Abs
from apps.core.models import User
from apps.cost.models import Cost


class BudgetQuerySet(models.QuerySet): # type: ignore
    def with_transaction_stats(self):
        from apps.transaction.models import Transaction

        spent_subquery = Transaction.objects.filter(
            user=OuterRef('user'),
            date__gte=OuterRef('start_date'),
            date__lte=OuterRef('end_date'),
            amount__lt=0
        ).exclude(
            purchase_type__iexact="Internal Transfer"
        ).values('user').annotate(
            total=Sum('amount')
        ).values('total')

        income_subquery = Transaction.objects.filter(
            user=OuterRef('user'),
            date__gte=OuterRef('start_date'),
            date__lte=OuterRef('end_date'),
            amount__gt=0
        ).exclude(
            purchase_type__iexact="Internal Transfer"
        ).values('user').annotate(
            total=Sum('amount')
        ).values('total')

        return self.annotate(
            annotated_costs=Coalesce(
                Sum('allocations__cost_amount'),
                Value(0),
                output_field=DecimalField()
            ),
            annotated_spend=Abs(Coalesce(
                Subquery(spent_subquery),
                Value(0),
                output_field=DecimalField()
            )),
            annotated_income=Coalesce(
                Subquery(income_subquery),
                Value(0),
                output_field=DecimalField()
            )
        )


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

    objects = BudgetQuerySet.as_manager()

    def __str__(self):
        return f"Budget {self.id} {self.start_date} -> {self.end_date}"

    def get_total_costs(self):
        result = self.allocations.aggregate(total=Sum('cost_amount'))
        return result['total'] or 0

    def get_categorised_transactions(self):
        from apps.transaction.models import Transaction

        all_transactions = Transaction.objects.filter(
            user=self.user,
            date__range=[self.start_date, self.end_date]
        ).exclude(
            purchase_type__iexact="Internal Transfer"
        ).order_by('-date')

        transaction_types = {
            'outgoing': [],
            'incoming': []
        }

        for transaction in all_transactions:
            if transaction.amount < 0:
                transaction_types['outgoing'].append(transaction)
            else:
                transaction_types['incoming'].append(transaction)

        return transaction_types


class CostAllocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    budget_period = models.ForeignKey(
        BudgetPeriod,
        on_delete=models.CASCADE,
        related_name='allocations',
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
