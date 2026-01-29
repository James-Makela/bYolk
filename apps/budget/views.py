from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.budget.filters import BudgetFilter
from apps.budget.models import Budget


# Create your views here.
def budgets_page(request):
    return render(request, 'budget/index.html')


@login_required
def budgets_list(request):
    budget_filter = BudgetFilter(
        request.GET,
        queryset=Budget.objects.filter(user=request.user)
    )
    context = {'filter': budget_filter}
    return render(request, 'budget/index.html', context)
