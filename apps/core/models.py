from datetime import date
from django.db import models
from django.contrib.auth.models import AbstractUser


class FrequencyUnit(models.TextChoices):
    DAY = 'day', 'Day(s)'
    WEEK = 'week', 'Week(s)'
    MONTH = 'month', 'Month(s)'
    YEAR = 'year', 'Year(s)'


# Create your models here.
class User(AbstractUser):
    budget_type = models.CharField(
        max_length=10,
        choices=FrequencyUnit.choices,
        default=FrequencyUnit.DAY
    )
    budget_interval = models.PositiveIntegerField(
        default=14,
        help_text="Days for 'Fixed Days', or the date (1-31) for 'Day of Month'."
    )
    start_pay_date = models.DateField(default=date.today)


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name}"

