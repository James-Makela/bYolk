from apps.core.models import FinancialItem


class Income(FinancialItem):
    class Meta:
        ordering = ["-amount"]

    def __str__(self):
        return f"${self.amount} from {self.name} for {self.user}"
