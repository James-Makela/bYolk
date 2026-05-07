from django.db import models

from apps.budget.models import CostAllocation
from apps.core.models import User


# Create your models here.
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    vendor = models.CharField(max_length=255, null=True, blank=True)
    purchase_type = models.CharField(max_length=255, null=True, blank=True)
    receipt_details = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    processed = models.BooleanField(default=False)
    unique_hash = models.CharField(max_length=30, unique=True, db_index=True)
    cost_allocation = models.ForeignKey(
        CostAllocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    @property
    def is_positive(self):
        if self.amount > 0:
            return True
        else:
            return False

    def __str__(self):
        return f"{self.date}, {self.vendor}"
