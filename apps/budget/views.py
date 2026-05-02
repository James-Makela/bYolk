from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from apps.budget.filters import BudgetPeriodFilter
from apps.budget.models import BudgetPeriod, CostAllocation
from apps.transaction.models import Transaction
from django.http import HttpResponse, Http404


@login_required
def budgets_list(request):
    budget_filter = BudgetPeriodFilter(
        request.GET,
        queryset=BudgetPeriod.objects.filter(user=request.user).order_by('-start_date')
    )
    context = {'filter': budget_filter}
    return render(request, 'budget/index.html', context)

@login_required
def budget_detail(request, budget_id):
    budget = get_object_or_404(BudgetPeriod, pk=budget_id, user=request.user)
    allocations = CostAllocation.objects.filter(budget_period=budget)
    matching_transactions = Transaction.objects.filter(
        user=request.user,
        date__range=[budget.start_date, budget.end_date]
    ).exclude(purchase_type__iexact="Internal Transfer").order_by('-date')

    return render(request, "budget/detail.html", {
        "budget": budget,
        "allocations": allocations,
        "matching_transactions": matching_transactions,
    })
