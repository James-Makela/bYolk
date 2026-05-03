from django.db import models

from apps.core.models import Category, FrequencyMixin, User
from apps.cost.managers import CostQuerySet


# Create your models here.
class Cost(FrequencyMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)
    start_date = models.DateField()
    keywords = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated list"
    )

    objects = CostQuerySet.as_manager()

    def __str__(self):
        return f"{self.name}, ${self.amount} every {self.frequency_value} \
    {self.frequency_unit}"

    def frequency_string(self):
        if self.frequency_value > 1:
            return f"Every {self.frequency_value} {self.frequency_unit.capitalize()}"
        else:
            return f"Every {self.frequency_value}\
            {self.frequency_unit.capitalize().rstrip('s')}"

    class Meta:
        ordering = ["-amount"]
