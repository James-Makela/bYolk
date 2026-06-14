from django.db import models

from apps.core.models import FrequencyMixin, KeywordsMixin, User


class Income(KeywordsMixin, FrequencyMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    keywords = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated list"
    )

    def __str__(self):
        return f"${self.amount} from {self.name} for {self.user}"

    class Meta:
        ordering = ["-amount"]

    @property
    def income_per_budget_period(self):
        length_of_budget_period = self.user.preferences.get_delta_days()
        return (self.amount / self.get_delta_days()) * length_of_budget_period

    @property
    def income_per_year(self):
        return (self.amount / self.get_delta_days()) * 365

    @property
    def income_per_week(self):
        return (self.amount / self.get_delta_days()) * 7
