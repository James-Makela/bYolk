from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.cost.models import Cost


# Create your views here.
def costs_page(request):
    return render(request, 'cost/index.html')


@login_required
def costs_list(request):
    costs = Cost.objects.filter(user=request.user)
    context = {'costs': costs}
    return render(request, 'cost/costs-list.html', context)
