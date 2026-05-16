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
