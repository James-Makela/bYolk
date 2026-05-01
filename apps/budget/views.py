from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from apps.budget.filters import BudgetPeriodFilter
from apps.budget.models import BudgetPeriod, CostAllocation
from django.http import HttpResponse, Http404


@login_required
def budgets_list(request):
    budget_filter = BudgetPeriodFilter(
        request.GET,
        queryset=BudgetPeriod.objects.filter(user=request.user)
    )
    context = {'filter': budget_filter}
    return render(request, 'budget/index.html', context)

@login_required
def budget_detail(request, budget_id):
    budget = get_object_or_404(BudgetPeriod, pk=budget_id, user=request.user)
    allocations = CostAllocation.objects.filter(budget_period=budget)
    return render(request, "budget/detail.html", {
        "budget": budget,
        "allocations": allocations,
    })
