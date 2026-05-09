from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.budget.models import BudgetPeriod, CostAllocation
from apps.transaction.models import Transaction

from .forms import CostAllocationForm, CostAllocationTransactionsForm
from .services import generate_next_budget_period, populate_from_costs


@login_required
def budgets_list(request):
    budget_periods = (
        BudgetPeriod.objects.filter(user=request.user)
        .with_transaction_stats()
        .order_by("-start_date")
    )

    context = {"budget_periods": budget_periods}
    return render(request, "budget/index.html", context)


@login_required
def budget_detail(request, id):
    budget = get_object_or_404(
        BudgetPeriod.objects.with_transaction_stats(), pk=id, user=request.user
    )
    previous = (
        BudgetPeriod.objects.filter(id__lt=id, user=request.user)
        .order_by("-id")
        .only("id")
        .first()
    )
    next = (
        BudgetPeriod.objects.filter(id__gt=id, user=request.user)
        .order_by("id")
        .only("id")
        .first()
    )
    allocations = CostAllocation.objects.filter(budget_period=budget).prefetch_related(
        "transactions"
    )
    duplicate_names = (
        allocations.values("cost_name")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
        .values_list("cost_name", flat=True)
    )

    grouped_allocations = []
    for name in duplicate_names:
        items_list = allocations.filter(cost_name=name)
        total_paid = sum(item.total_paid for item in items_list)
        total_amount = sum(item.dynamic_cost_amount for item in items_list)
        remaining_spend = total_amount - total_paid
        grouped_allocations.append(
            {
                "name": name,
                "all_dates": [item.expected_date for item in items_list],
                "total_amount": total_amount,
                "total_paid": total_paid,
                "remaining_spend": remaining_spend,
                "original_items": items_list,
            }
        )

    ungrouped_allocations = allocations.exclude(cost_name__in=duplicate_names)

    context = {
        "budget": budget,
        "allocations": ungrouped_allocations,
        "grouped_allocations": grouped_allocations,
        "previous": previous,
        "next": next,
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

    transactions = allocation.budget_period.get_categorised_transactions()
    unallocated = list(transactions["allocatable"])

    if not allocation.cost or len(allocation.cost.keywords) == 0:
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
        update_amount = "update_amount" in request.POST

        # Link selected transactions to this allocation
        Transaction.objects.filter(id__in=selected_ids, user=request.user).update(
            cost_allocation=allocation
        )
        if update_amount:
            total_sum = (
                Transaction.objects.filter(cost_allocation=allocation).aggregate(
                    total=Sum("amount")
                )["total"]
                or 0
            )

            allocation.cost_amount = abs(total_sum)
            allocation.save()

        # HX-Refresh tells the browser to reload the whole page to update totals
        response = HttpResponse("Saved")
        response["HX-Refresh"] = "true"
        return response


@login_required
def add_single_allocation(request, budget_id):
    budget_period = get_object_or_404(BudgetPeriod, id=budget_id)

    if request.method == "POST":
        form = CostAllocationForm(request.POST)
        if form.is_valid():
            new_allocation = form.save(commit=False)
            new_allocation.budget_period = budget_period
            new_allocation.save()
            messages.success(request, "Cost added!")
            return HttpResponseRedirect(f"/budgets/{budget_id}")

        else:
            messages.error(request, "Unable to save cost.")
            return HttpResponseRedirect(f"/budgets/{budget_id}")

    else:
        form = CostAllocationForm(user=request.user)

    return render(
        request,
        "budget/forms/add_allocation_form.html",
        {
            "budget_id": budget_id,
            "form": form,
        },
    )


@login_required
def add_allocation_with_transactions(request, budget_id):
    budget_period = get_object_or_404(BudgetPeriod, id=budget_id)

    if request.method == "POST":
        form = CostAllocationForm(request.POST)
        selected_ids = request.POST.getlist("transaction_ids")
        if form.is_valid():
            new_allocation = form.save(commit=False)
            new_allocation.budget_period = budget_period
            new_allocation.save()

            Transaction.objects.filter(id__in=selected_ids, user=request.user).update(
                cost_allocation=new_allocation
            )
            messages.success(request, "Cost added!")
            return HttpResponseRedirect(f"/budgets/{budget_id}")

        else:
            messages.error(request, "Unable to save cost.")
            return HttpResponseRedirect(f"/budgets/{budget_id}")

    else:
        transaction_ids = request.GET.getlist("transaction_ids")
        selected_transactions = Transaction.objects.filter(
            user=request.user,
            id__in=transaction_ids,
        )
        total_amount = sum(abs(tx.amount) for tx in selected_transactions)
        form = CostAllocationTransactionsForm(
            user=request.user, initial={"cost_amount": total_amount}
        )

    return render(
        request,
        "budget/forms/add_allocation_with_transactions_form.html",
        {
            "budget_id": budget_id,
            "form": form,
            "total": total_amount,
            "selected_transactions": selected_transactions,
        },
    )


@login_required
def move_cost_allocation(request, allocation_id, budget_id):
    allocation = get_object_or_404(
        CostAllocation.objects.select_related("budget_period"),
        pk=allocation_id,
        budget_period__user=request.user,
    )

    current_budget = allocation.budget_period.id
    try:
        budget_to_assign = BudgetPeriod.objects.get(pk=budget_id)
    except BudgetPeriod.DoesNotExist:
        budget_to_assign = None

    if not budget_to_assign:
        messages.error(
            request,
            "The budget you are trying to move this allocation to does not exist.",
        )
    else:
        allocation.budget_period = budget_to_assign
        allocation.save()
        messages.success(request, "Allocation moved successfully.")

    return HttpResponseRedirect(f"/budgets/{current_budget}")


@login_required
def delete_allocation(request, pk, budget_id):
    allocation = get_object_or_404(
        CostAllocation, pk=pk, budget_period__user=request.user
    )

    if request.method == "POST":
        allocation.delete()
        messages.success(request, "Allocation deleted")

    return HttpResponseRedirect(f"/budgets/{budget_id}")
