from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from apps.budget.filters import BudgetFilter
from apps.budget.models import Budget
from django.http import HttpResponse, Http404


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

@login_required
def budget_detail(request, budget_id):
    budget = get_object_or_404(Budget, pk=budget_id)
    return render(request, "budget/detail.html", {"budget": budget})
