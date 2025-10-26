from django.db import models
from apps.core.models import User


# Create your models here.
class Budget(models.Model):
    FREQUENCY_UNITS = [
        ("days", "Days"),
        ("weeks", "Weeks"),
        ("months", "Months"),
        ("years", "Years"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    frequency_number = models.IntegerField()
    frequency_unit = models.CharField(max_length=50, choices=FREQUENCY_UNITS)
    anchor_date = models.DateField()
