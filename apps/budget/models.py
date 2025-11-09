from django.db import models
from apps.core.models import User
from apps.cost.models import Cost


class BudgetPeriod(models.Model):
    FREQUENCY_UNITS = [
        ("days", "Days"),
        ("weeks", "Weeks"),
        ("months", "Months"),
        ("years", "Years"),
    ]

    anchor_date = models.DateField()
    frequency_number = models.IntegerField()
    frequency_unit = models.CharField(max_length=50, choices=FREQUENCY_UNITS)


# Create your models here.
class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

    @property
    def costs(self):
        """We want all the costs that fit within the budget dates"""
        return Cost.objects.filter(
            anchor_date__gte=self.start_date,
            anchor_date__lte=self.end_date
        )
