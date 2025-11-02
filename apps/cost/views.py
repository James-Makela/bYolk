from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.cost.filters import CostFilter
from apps.cost.models import Cost


# Create your views here.
def costs_page(request):
    return render(request, 'cost/index.html')


@login_required
def costs_list(request):
    cost_filter = CostFilter(
        request.GET,
        queryset=Cost.objects.filter(user=request.user)
    )
    context = {'filter': cost_filter}
    return render(request, 'cost/index.html', context)
