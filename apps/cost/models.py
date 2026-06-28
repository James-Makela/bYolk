from django.db import models
from django.utils import timezone

from apps.core.models import Category, FinancialItem


class Cost(FinancialItem):
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["-amount"]

    def __str__(self):
        frequency_string = super().frequency_string()
        if frequency_string:
            frequency_string = frequency_string[0].lower() + frequency_string[1:]
        return f"{self.name}, ${self.amount} {frequency_string}"

    @property
    def passed(self):
        if self.end_date and self.end_date < timezone.now().date():
            return True
