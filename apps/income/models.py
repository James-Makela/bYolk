from django.db import models

from apps.core.models import FinancialChange, FinancialItem


class Income(FinancialItem):
    class Meta:
        ordering = ["-amount"]

    def __str__(self):
        return f"${self.amount} from {self.name} for {self.user}"


class IncomeChange(FinancialChange):
    income = models.ForeignKey(Income, on_delete=models.CASCADE)
