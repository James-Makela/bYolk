from django.db import models, transaction

from apps.core.models import User


# Create your models here.
class AssetBase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=10, decimal_places=2)


class PropertyAsset(AssetBase):
    amount_owing = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    @property
    def net_value(self):
        return self.value - self.amount_owing


class SavingsAccount(AssetBase):
    interest_rate = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        models.UniqueConstraint(
            fields=["user"],
            condition=models.Q(is_primary=True),
            name="one_primary_savings_per_user",
        )

    def save(self, *args, **kwargs):
        if self.is_primary:
            with transaction.atomic():
                SavingsAccount.objects.filter(user=self.user, is_primary=True).exclude(
                    pk=self.pk
                ).update(is_primary=False)

        super().save(*args, **kwargs)
