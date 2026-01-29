import django_filters
from apps.budget.models import Budget


class BudgetFilter(django_filters.FilterSet):
    start_date = django_filters.ChoiceFilter(
        choices=Budget.objects.all,
        field_name='start_date',
        lookup_expr='iexact',
        empty_label='All',
    )

    class Meta:
        model = Budget
        fields = ('start_date',)
