from django.db import models
from django.db.models import Count, DecimalField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Abs, Coalesce
from django.utils.functional import cached_property

from apps.core.models import Category, User
from apps.cost.models import Cost
from apps.income.models import Income


class BudgetQuerySet(models.QuerySet):  # type: ignore
    def with_transaction_stats(self):
        from apps.transaction.models import Transaction

        spent_subquery = (
            Transaction.objects.filter(
                user=OuterRef("user"),
                date__gte=OuterRef("start_date"),
                date__lte=OuterRef("end_date"),
                amount__lt=0,
            )
            .exclude(purchase_type__iexact="Internal Transfer")
            .values("user")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        income_subquery = (
            Transaction.objects.filter(
                user=OuterRef("user"),
                date__gte=OuterRef("start_date"),
                date__lte=OuterRef("end_date"),
                amount__gt=0,
            )
            .exclude(purchase_type__iexact="Internal Transfer")
            .values("user")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        return self.annotate(
            annotated_costs=Coalesce(
                Sum("costallocation_set__amount"), Value(0), output_field=DecimalField()
            ),
            annotated_spend=Abs(
                Coalesce(
                    Subquery(spent_subquery), Value(0), output_field=DecimalField()
                )
            ),
            annotated_income=Coalesce(
                Subquery(income_subquery), Value(0), output_field=DecimalField()
            ),
        )


class CostAllocationQuerySet(models.QuerySet):  # type: ignore
    def grouped_by_name(self):
        duplicate_names = (
            self.values("name")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
            .values_list("name", flat=True)
        )

        grouped = []
        for name in duplicate_names:
            items = list(self.filter(name=name).prefetch_related("transactions"))
            total_paid = sum(item.total_paid for item in items)
            total_amount = sum(item.amount for item in items)
            grouped.append(
                {
                    "name": name,
                    "all_dates": [item.expected_date for item in items],
                    "total_amount": total_amount,
                    "total_paid": total_paid,
                    "remaining_spend": total_amount - total_paid,
                    "original_items": items,
                }
            )

        return grouped


class BudgetPeriod(models.Model):
    objects = BudgetQuerySet.as_manager()

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        PENDING = "pending", "Pending"

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

    @cached_property
    def get_total_costs(self):
        result = self.costallocation_set.aggregate(total=Sum("amount"))
        return result["total"] or 0

    @cached_property
    def get_total_income(self):
        result = self.incomeallocation_set.aggregate(total=Sum("amount"))
        return result["total"] or 0

    @cached_property
    def balance(self):
        return self.get_total_income - self.get_total_costs

    def get_categorised_transactions(self):
        from apps.transaction.models import Transaction

        all_transactions = (
            Transaction.objects.filter(
                user=self.user, date__range=[self.start_date, self.end_date]
            )
            .exclude(purchase_type__iexact="Internal Transfer")
            .order_by("-date")
        )

        transaction_types = {
            "outgoing": [],
            "incoming": [],
            "unallocated": [],
        }

        for transaction in all_transactions:
            if (
                transaction.cost_allocation_id is None
                and transaction.income_allocation_id is None
            ):
                transaction_types["unallocated"].append(transaction)
            if transaction.amount < 0:
                transaction_types["outgoing"].append(transaction)
            elif transaction.cost_allocation_id is None:
                transaction_types["incoming"].append(transaction)

        return transaction_types


class AllocationBase(models.Model):
    budget_period = models.ForeignKey(
        BudgetPeriod,
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
    )
    name = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    expected_date = models.DateField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def total_paid(self):
        return sum(transaction.amount for transaction in self.transactions.all())

    @property
    def remaining(self):
        if self.total_paid >= 0:
            return self.amount - self.total_paid
        else:
            return self.amount + self.total_paid

    def __str__(self):
        return f"{self.name} ${self.amount} for Budget {self.budget_period_id}"


class CostAllocation(AllocationBase):
    objects = CostAllocationQuerySet.as_manager()

    cost = models.ForeignKey(Cost, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cost", "expected_date"],
                condition=models.Q(expected_date__isnull=False),
                name="unique_cost_per_budget",
            )
        ]
        ordering = ["-amount"]


class IncomeAllocation(AllocationBase):
    income = models.ForeignKey(Income, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["budget_period", "income", "expected_date"],
                name="unique_income_per_budget",
            )
        ]
