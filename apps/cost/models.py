from django.db import models
from apps.core.models import User, Category
from datetime import date

from apps.cost.managers import CostQuerySet


# Create your models here.
class Cost(models.Model):
    FREQUENCY_UNIT_CHOICES = [
        ("days", "Days"),
        ("weeks", "Weeks"),
        ("months", "Months"),
        ("years", "Years"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)
    frequency_number = models.IntegerField()
    frequency_unit = models.CharField(max_length=50, choices=FREQUENCY_UNIT_CHOICES)
    last_paid_date = models.DateField(null=True, blank=True)

    objects = CostQuerySet.as_manager()

    def __str__(self):
        return f"{self.name}, ${self.amount} every {self.frequency_number} \
    {self.frequency_unit}"

    def frequency_string(self):
        return f"Every {self.frequency_number} {self.frequency_unit}"

    class Meta():
        ordering = ['-amount']
