import uuid

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
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
        unit = self.get_frequency_unit_display()  # type: ignore
        if self.frequency_value == 1:
            unit = unit.rstrip("(s)")
            value = ""
        else:
            unit = unit.replace("(", "").replace(")", "")
            value = f"{self.frequency_value} "
        return f"Every {value}{unit}"


class KeywordsMixin:
    keywords: str

    def get_keywords(self):
        if not self.keywords:
            return []
        return [
            keyword.strip().lower()
            for keyword in self.keywords.split(",")
            if keyword.strip()
        ]


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


# Create your models here.
class User(AbstractUser):
    username = None  # type: ignore
    email = models.EmailField(unique=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()  # type: ignore


class UserPreferences(FrequencyMixin, models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences"
    )
    first_budget_date = models.DateField(default=timezone.now)

    class Meta:
        verbose_name_plural = "User Preferences"

    def __str__(self):
        return f"Preferences for {self.user.email}"


class FinancialItem(KeywordsMixin, FrequencyMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    keywords = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated list"
    )

    class Meta:
        abstract = True
        ordering = ["-amount"]

    @property
    def per_budget_period(self):
        length_of_budget_period = self.user.preferences.get_delta_days()
        return (self.amount / self.get_delta_days()) * length_of_budget_period

    @property
    def per_year(self):
        return (self.amount / self.get_delta_days()) * 365

    @property
    def per_week(self):
        return (self.amount / self.get_delta_days()) * 7


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
