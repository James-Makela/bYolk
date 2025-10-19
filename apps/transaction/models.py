from django.db import models
from apps.core.models import User


# Create your models here.
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    vendor = models.CharField(max_length=255)
    purchase_type = models.CharField(max_length=255)
    receipt_number = models.CharField(max_length=255)
    credit = models.DecimalField(max_digits=10, decimal_places=2)
    debit = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
