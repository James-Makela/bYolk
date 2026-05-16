from django.db import models

from apps.core.models import Category, FrequencyMixin, KeywordsMixin, User


class Cost(KeywordsMixin, FrequencyMixin, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL
    )
    start_date = models.DateField()
    keywords = models.CharField(
        max_length=500, blank=True, help_text="Comma-separated list"
    )

    class Meta:
        ordering = ["-amount"]

    def __str__(self):
        frequency_string = super().frequency_string()
        if frequency_string:
            frequency_string = frequency_string[0].lower() + frequency_string[1:]
        return f"{self.name}, ${self.amount} {frequency_string}"

    @property
    def cost_per_budget_period(self):
        length_of_budget_period = self.user.preferences.get_delta_days()
        return (self.amount / self.get_delta_days()) * length_of_budget_period
