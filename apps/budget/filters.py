import django_filters
from apps.budget.models import BudgetPeriod


class BudgetPeriodFilter(django_filters.FilterSet):
    class Meta:
        model = BudgetPeriod
        fields = ('start_date', 'status')
