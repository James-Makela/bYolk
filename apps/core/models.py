from datetime import date
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class FrequencyMixin(models.Model):
    """
    This will be the shared logic for working out time intervals for classes with recurring intervals
    """
    class FrequencyUnit(models.TextChoices):
        DAY = 'days', 'Day(s)'
        WEEK = 'weeks', 'Week(s)'
        MONTH = 'months', 'Month(s)'
        YEAR = 'years', 'Year(s)'

    frequency_value = models.PositiveIntegerField(default=1)
    frequency_unit = models.CharField(
        max_length=10,
        choices=FrequencyUnit,
        default=FrequencyUnit.MONTH
    )

    class Meta:
        abstract = True

    def get_delta(self):
        kwargs = {self.frequency_unit: self.frequency_value}
        return relativedelta(**kwargs)

    def __eq__(self, other):
        if not hasattr(other, 'get_delta'):
            return False
        return self.get_delta() == other.get_delta()


# Create your models here.
class User(AbstractUser):
    pass


class UserPreferences(FrequencyMixin, models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    first_pay_date = models.DateField(default=timezone.now)

    class Meta:
        verbose_name_plural = "User Preferences"

    def __str__(self):
        return f"Preferences for {self.user.username}"


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name}"

