from django.db import models
from apps.core.models import User
from datetime import date

from apps.cost.managers import CostQuerySet


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name}"


# Create your models here.
class Cost(models.Model):
    FREQUENCY_UNITS = [
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
    frequency_unit = models.CharField(max_length=50, choices=FREQUENCY_UNITS)
    anchor_date = models.DateField(default=date.today)

    objects = CostQuerySet.as_manager()

    def __str__(self):
        return f"{self.name}, ${self.amount} every {self.frequency_number} \
    {self.frequency_unit}"

    def frequency_string(self):
        return f"Every {self.frequency_number} {self.frequency_unit}"

    class Meta():
        ordering = ['-amount']
