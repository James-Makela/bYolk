from django.db import models
from apps.core.models import User


# Create your models here.
class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anchor_date = models.DateField()
    budget_period = models.DurationField()
