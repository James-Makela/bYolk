import django_filters

from apps.transaction.models import Transaction


class TransactionFilter(django_filters.FilterSet):
    transaction_category = django_filters.ChoiceFilter(
        choices=Transaction.objects.all,
        field_name="purchase_type",
        lookup_expr="iexact",
        empty_label="Any",
    )

    class Meta:
        model = Transaction
        fields = ("purchase_type",)
