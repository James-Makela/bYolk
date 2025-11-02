import django_filters
from apps.cost.models import Category, Cost


class CostFilter(django_filters.FilterSet):
    cost_category = django_filters.ChoiceFilter(
            choices=Category.objects.all,
            field_name='category',
            lookup_expr='iexact',
            empty_label='Any',
    )

    class Meta:
        model = Cost
        fields = ('category',)
