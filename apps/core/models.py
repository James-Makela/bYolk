from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class User(AbstractUser):
    class PayFrequency(models.TextChoices):
        DAYS = 'days', 'Fixed number of Days'
        MONTHLY = 'monthly', 'Day of Month'

    budget_type = models.CharField(
        max_length=10,
        choices=PayFrequency.choices,
        default=PayFrequency.DAYS
    )
    budget_interval_value = models.PositiveIntegerField(
        default=14,
        help_text="Days for 'Fixed Days', or the date (1-31) for 'Day of Month'."
    )


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name}"
