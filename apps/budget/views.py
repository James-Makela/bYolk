from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.budget.filters import BudgetPeriodFilter
from apps.budget.models import BudgetPeriod, CostAllocation
from apps.transaction.models import Transaction

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
def budget_detail(request, id):
    budget = get_object_or_404(
        BudgetPeriod.objects.with_transaction_stats(), pk=id, user=request.user
    )
    allocations = CostAllocation.objects.filter(budget_period=budget).prefetch_related(
        "transactions"
    )
    context = {
        "budget": budget,
        "allocations": allocations,
        "previous": BudgetPeriod.objects.filter(id__lt=id)
        .order_by("-id")
        .only("id")
        .first(),
        "next": BudgetPeriod.objects.filter(id__gt=id)
        .order_by("id")
        .only("id")
        .first(),
    }

    return render(
        request,
        "budget/detail.html",
        context,
    )


@login_required
def start_next_budget(request):
    print(f"User: {request.user}")
    generate_next_budget_period(request.user)
    messages.success(request, "Next budget period generated")
    return HttpResponseRedirect("/budgets/")


@login_required
def populate_costs(request, id):
    budget_period = get_object_or_404(BudgetPeriod, pk=id, user=request.user)
    populate_from_costs(budget_period, request.user)
    messages.success(request, "Costs populated")
    return HttpResponseRedirect(reverse("detail", args=[id]))


@login_required
def get_allocation_picker(request, allocation_id):
    """Returns the HTMX modal content for selecting transactions."""
    allocation = get_object_or_404(
        CostAllocation.objects.select_related("budget_period"),
        pk=allocation_id,
        budget_period__user=request.user,
    )

    # This now contains the 'unallocated' key thanks to the model update above
    transactions = allocation.budget_period.get_categorised_transactions()
    unallocated = list(transactions["unallocated"])

    if len(allocation.cost.keywords) == 0:
        keywords = None
    else:
        keywords = allocation.cost.keywords.split(",")

    for transaction in unallocated:
        if not keywords:
            break
        for keyword in keywords:
            if keyword.lower().strip() in transaction.vendor.lower():
                print(f"Matched {keyword} against {transaction.vendor}")
                transaction.is_match = True

    sorted_transactions = sorted(
        unallocated, key=lambda x: getattr(x, "is_match", False), reverse=True
    )

    return render(
        request,
        "budget/partials/allocation_modal.html",
        {
            "allocation": allocation,
            "eligible_transactions": sorted_transactions,
        },
    )


@login_required
def save_allocations(request, allocation_id):
    """Processes the HTMX form submission."""
    allocation = get_object_or_404(
        CostAllocation.objects.select_related("budget_period"),
        pk=allocation_id,
        budget_period__user=request.user,
    )

    if request.method == "POST":
        selected_ids = request.POST.getlist("transaction_ids")

        # Link selected transactions to this allocation
        Transaction.objects.filter(id__in=selected_ids, user=request.user).update(
            cost_allocation=allocation
        )

        # HX-Refresh tells the browser to reload the whole page to update totals
        response = HttpResponse("Saved")
        response["HX-Refresh"] = "true"
        return response
