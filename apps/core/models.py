from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class FrequencyMixin(models.Model):
    """
    This will be the shared logic for working out
    time intervals for classes with recurring intervals
    """

    class FrequencyUnit(models.TextChoices):
        DAY = "days", "Day(s)"
        WEEK = "weeks", "Week(s)"
        MONTH = "months", "Month(s)"
        YEAR = "years", "Year(s)"

    frequency_value = models.PositiveIntegerField(default=1)
    frequency_unit = models.CharField(
        max_length=10, choices=FrequencyUnit, default=FrequencyUnit.MONTH
    )

    class Meta:
        abstract = True

    def get_delta(self):
        kwargs = {self.frequency_unit: self.frequency_value}
        return relativedelta(**kwargs)

    def get_delta_days(self):
        relative_delta = self.get_delta()
        return (
            relative_delta.days
            + (relative_delta.months * 30)
            + (relative_delta.years * 365)
        )

    def matches_frequency(self, other):
        if not hasattr(other, "get_delta"):
            return False
        return self.get_delta() == other.get_delta()

    def frequency_string(self):
        unit = self.get_frequency_unit_display()
        if self.frequency_value == 1:
            unit = unit.rstrip("(s)")
            value = ""
        else:
            unit = unit.replace("(", "").replace(")", "")
            value = f"{self.frequency_value} "
        return f"Every {value}{unit}"


# Create your models here.
class User(AbstractUser):
    pass


class UserPreferences(FrequencyMixin, models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences"
    )
    first_budget_date = models.DateField(default=timezone.now)

    class Meta:
        verbose_name_plural = "User Preferences"

    def __str__(self):
        return f"Preferences for {self.user.username}"


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        constraints = [
            models.UniqueConstraint(
                "user",
                Lower("name"),
                name="unique_category_per_user",
            )
        ]

    def __str__(self):
        return f"{self.name}"
