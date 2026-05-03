from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.budget.filters import BudgetPeriodFilter
from apps.budget.models import BudgetPeriod, CostAllocation

from .services import generate_next_budget_period, populate_from_costs


@login_required
def budgets_list(request):
    qs = (
        BudgetPeriod.objects.filter(user=request.user)
        .with_transaction_stats()
        .order_by("-start_date")
    )

    budget_filter = BudgetPeriodFilter(request.GET, queryset=qs)
    context = {"filter": budget_filter}
    return render(request, "budget/index.html", context)


@login_required
def budget_detail(request, budget_id):
    budget = get_object_or_404(
        BudgetPeriod.objects.with_transaction_stats(), pk=budget_id, user=request.user
    )
    allocations = CostAllocation.objects.filter(budget_period=budget)

    return render(
        request,
        "budget/detail.html",
        {
            "budget": budget,
            "allocations": allocations,
        },
    )


@login_required
def start_next_budget(request):
    print(f"User: {request.user}")
    generate_next_budget_period(request.user)
    messages.success(request, "Next budget period generated")
    return HttpResponseRedirect("/budgets/")


@login_required
def populate_costs(request, budget_id):
    budget_period = get_object_or_404(BudgetPeriod, pk=budget_id, user=request.user)
    populate_from_costs(budget_period, request.user)
    messages.success(request, "Costs populated")
    return HttpResponseRedirect(reverse("detail", args=[budget_id]))
