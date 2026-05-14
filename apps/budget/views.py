from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import BooleanField, Case, Count, Sum, Value, When
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from apps.budget.models import BudgetPeriod, CostAllocation, IncomeAllocation
from apps.core.forms import InitialUserPreferencesForm
from apps.transaction.models import Transaction

from .forms import CostAllocationForm, CostAllocationTransactionsForm
from .services import generate_next_budget_period, populate_from_costs


@login_required
def budgets_list(request):
    today = timezone.now().date()
    budget_periods = (
        BudgetPeriod.objects.filter(user=request.user)
        .annotate(
            is_current_period=Case(
                When(start_date__lte=today, end_date__gte=today, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        .with_transaction_stats()
        .order_by("-start_date")
    )

    current_budget = budget_periods.filter(is_current_period=True).first()

    context = {
        "budget_periods": budget_periods,
        "current_budget": current_budget,
        "form": None,
    }
    if not hasattr(request.user, "preferences"):
        context["form"] = InitialUserPreferencesForm()
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
        allocations.values("name")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
        .values_list("name", flat=True)
    )

    incomes = IncomeAllocation.objects.filter(budget_period=budget).prefetch_related(
        "transactions"
    )

    unallocated_transactions = budget.get_categorised_transactions()["unallocated"]
    unallocated_balance = sum(
        transaction.amount for transaction in unallocated_transactions
    )

    grouped_allocations = []
    for name in duplicate_names:
        items_list = allocations.filter(name=name)
        total_paid = sum(item.total_paid for item in items_list)
        total_amount = sum(item.amount for item in items_list)
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

    ungrouped_allocations = allocations.exclude(name__in=duplicate_names)

    context = {
        "budget": budget,
        "allocations": ungrouped_allocations,
        "grouped_allocations": grouped_allocations,
        "incomes": incomes,
        "previous": previous,
        "next": next,
        "unallocated_balance": unallocated_balance,
        "unallocated_transactions": unallocated_transactions,
    }

    return render(
        request,
        "budget/detail.html",
        context,
    )


@login_required
def start_next_budget(request):
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
def get_allocation_picker(request, allocation_type, allocation_id):
    """Returns the HTMX modal content for selecting transactions."""
    models = {
        "income": IncomeAllocation,
        "cost": CostAllocation,
    }
    TargetModel = models.get(allocation_type, CostAllocation)
    related_field = "cost" if allocation_type == "cost" else "income"

    allocation = get_object_or_404(
        TargetModel.objects.select_related("budget_period"),
        pk=allocation_id,
        budget_period__user=request.user,
    )

    transactions = allocation.budget_period.get_categorised_transactions()
    unallocated = list(transactions["unallocated"])

    source_obj = getattr(allocation, related_field, None)

    keywords = None
    if source_obj and source_obj.keywords:
        keywords = [
            k.strip().lower() for k in source_obj.keywords.split(",") if k.strip()
        ]

    for transaction in unallocated:
        transaction.is_match = False
        if keywords and transaction.vendor:
            vendor_lower = transaction.vendor.lower()
            if any(kw in vendor_lower for kw in keywords):
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
            "allocation_type": allocation_type,
        },
    )


@login_required
def save_allocations(request, allocation_type, allocation_id):
    """Processes the HTMX form submission."""
    models = {
        "income": IncomeAllocation,
        "cost": CostAllocation,
    }
    TargetModel = models.get(allocation_type, CostAllocation)
    field_to_update = (
        "income_allocation" if allocation_type == "income" else "cost_allocation"
    )

    allocation = get_object_or_404(
        TargetModel.objects.select_related("budget_period"),
        pk=allocation_id,
        budget_period__user=request.user,
    )

    if request.method == "POST":
        selected_ids = request.POST.getlist("transaction_ids")
        update_amount = "update_amount" in request.POST

        # Link selected transactions to this allocation
        Transaction.objects.filter(id__in=selected_ids, user=request.user).update(
            **{field_to_update: allocation}
        )

        if update_amount:
            total_sum = (
                Transaction.objects.filter(**{field_to_update: allocation}).aggregate(
                    total=Sum("amount")
                )["total"]
                or 0
            )

            allocation.amount = abs(total_sum)
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
def edit_allocation_with_transactions(request, budget_id, pk=None):
    budget_period = get_object_or_404(BudgetPeriod, id=budget_id)

    if pk:
        allocation = get_object_or_404(
            CostAllocation, pk=pk, budget_period__user=request.user
        )
        title = "Edit Allocation"
        message = "Allocation updated!"
        total_allocated = allocation.amount
    else:
        allocation = None
        title = "Add Allocation"
        message = "Allocation saved!"

    if request.method == "POST":
        form = CostAllocationForm(request.POST, instance=allocation)
        selected_ids = request.POST.getlist("transaction_ids")
        if form.is_valid():
            new_allocation = form.save(commit=False)
            new_allocation.budget_period = budget_period
            new_allocation.save()

            # Allocate ticked transactions
            Transaction.objects.filter(id__in=selected_ids, user=request.user).update(
                cost_allocation=new_allocation
            )
            # Unallocate any unticked
            Transaction.objects.filter(
                cost_allocation=new_allocation, user=request.user
            ).exclude(id__in=selected_ids).update(cost_allocation=None)

            messages.success(request, message)
            return HttpResponseRedirect(f"/budgets/{budget_id}")

        else:
            messages.error(request, "Unable to save cost.")
            return HttpResponseRedirect(f"/budgets/{budget_id}")

    else:
        transaction_ids = request.GET.getlist("transaction_ids")
        if not transaction_ids and allocation:
            transaction_ids = allocation.transactions.values_list("id", flat=True)
        selected_transactions = Transaction.objects.filter(
            user=request.user,
            id__in=transaction_ids,
        )
        if not total_allocated:
            total_allocated = abs(sum((tx.amount) for tx in selected_transactions))
        form = CostAllocationTransactionsForm(
            instance=allocation, user=request.user, initial={"amount": total_allocated}
        )

    return render(
        request,
        "budget/forms/add_allocation_with_transactions_form.html",
        {
            "budget_id": budget_id,
            "form": form,
            "total": total_allocated,
            "selected_transactions": selected_transactions,
            "title": title,
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
def delete_allocation(request, allocation_type, pk, budget_id):
    models = {
        "income": IncomeAllocation,
        "cost": CostAllocation,
    }
    TargetModel = models.get(allocation_type, CostAllocation)

    allocation = get_object_or_404(TargetModel, pk=pk, budget_period__user=request.user)

    if request.method == "POST":
        allocation.delete()
        messages.success(request, "Allocation deleted")

    return HttpResponseRedirect(f"/budgets/{budget_id}")


@login_required
def delete_budget_period(request, pk):
    period = get_object_or_404(BudgetPeriod, pk=pk, user=request.user)

    if request.method == "POST":
        period.delete()
        messages.success(request, "Budget Period deleted")

    return HttpResponseRedirect("/budgets/")
