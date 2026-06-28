from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import BooleanField, Case, Sum, Value, When
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from apps.budget.models import Bucket, BudgetPeriod, CostAllocation, IncomeAllocation
from apps.core.forms import InitialUserPreferencesForm
from apps.transaction.models import Transaction

from .forms import (
    BucketForm,
    CostAllocationForm,
    CostAllocationTransactionsForm,
    IncomeAllocationTransactionsForm,
)
from .services import generate_next_budget_period, populate_from_costs


@login_required
def budgets_list(request):
    today = timezone.now().date()
    budget_periods = (
        BudgetPeriod.objects.filter(user=request.user)  # type: ignore
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
        BudgetPeriod.objects.with_transaction_stats(),  # type: ignore
        pk=id,
        user=request.user,
    )
    previous_period = (
        BudgetPeriod.objects.filter(id__lt=id, user=request.user)
        .order_by("-id")
        .only("id")
        .first()
    )
    next_period = (
        BudgetPeriod.objects.filter(id__gt=id, user=request.user)
        .order_by("id")
        .only("id")
        .first()
    )

    allocations = CostAllocation.objects.filter(budget_period=budget).prefetch_related(
        "transactions"
    )

    grouped_allocations = allocations.grouped_by_name()  # type: ignore
    ungrouped_allocations = allocations.exclude(
        name__in=[g["name"] for g in grouped_allocations]
    )

    incomes = IncomeAllocation.objects.filter(budget_period=budget).prefetch_related(
        "transactions"
    )

    unallocated_transactions = budget.get_categorised_transactions()["unallocated"]
    unallocated_balance = sum(
        transaction.amount for transaction in unallocated_transactions
    )

    buckets = Bucket.objects.filter(user=request.user)

    budget_length = (budget.end_date - budget.start_date).days + 1
    current_position = (timezone.now().date() - budget.start_date).days + 1
    if current_position > budget_length:
        complete = True
    else:
        complete = False

    context = {
        "budget": budget,
        "allocations": ungrouped_allocations,
        "grouped_allocations": grouped_allocations,
        "incomes": incomes,
        "previous": previous_period,
        "next": next_period,
        "unallocated_balance": unallocated_balance,
        "unallocated_transactions": unallocated_transactions,
        "budget_length": budget_length,
        "current_position": current_position,
        "complete": complete,
        "buckets": buckets,
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
    return HttpResponseRedirect(reverse("budgets-page"))


@login_required
def populate_costs(request, id):
    budget_period = get_object_or_404(BudgetPeriod, pk=id, user=request.user)
    populate_from_costs(budget_period, request.user)
    messages.success(request, "Costs populated")
    return HttpResponseRedirect(reverse("detail", args=[id]))


@login_required
def get_allocation_picker(request, allocation_type, allocation_id):
    """Returns the HTMX modal content for selecting transactions."""
    TargetModel = CostAllocation if allocation_type == "cost" else IncomeAllocation

    related_field = "cost" if allocation_type == "cost" else "income"

    allocation = get_object_or_404(
        TargetModel.objects.select_related("budget_period"),
        pk=allocation_id,
        budget_period__user=request.user,
    )

    transactions = allocation.budget_period.get_categorised_transactions()
    unallocated = list(transactions["unallocated"])

    source_obj = getattr(allocation, related_field, None)

    keywords = source_obj.get_keywords() if source_obj else []

    for transaction in unallocated:
        transaction.is_match = transaction.matches_keywords(keywords)

    sorted_transactions = sorted(unallocated, key=lambda x: x.is_match, reverse=True)

    return render(
        request,
        "budget/partials/_allocation_modal.html",
        {
            "allocation": allocation,
            "eligible_transactions": sorted_transactions,
            "allocation_type": allocation_type,
        },
    )


@login_required
def save_allocations(request, allocation_type, allocation_id):
    """Processes the HTMX form submission."""
    TargetModel = CostAllocation if allocation_type == "cost" else IncomeAllocation
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

            allocation.amount = total_sum
            print("Fine till here")
            allocation.save()

        # HX-Refresh tells the browser to reload the whole page to update totals
        response = HttpResponse("Saved")
        response["HX-Refresh"] = "true"
        return response

    return HttpResponse(status=405)


@login_required
def add_single_allocation(request, budget_id):
    budget_period = get_object_or_404(BudgetPeriod, id=budget_id, user=request.user)

    if request.method == "POST":
        form = CostAllocationForm(request.POST)
        if form.is_valid():
            new_allocation = form.save(commit=False)
            new_allocation.budget_period = budget_period
            new_allocation.save()
            messages.success(request, "Cost added!")
            return HttpResponseRedirect(reverse("detail", args=[budget_id]))

        else:
            messages.error(request, "Unable to save cost.")
            return HttpResponseRedirect(reverse("detail", args=[budget_id]))

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
def edit_allocation_with_transactions(request, allocation_type, budget_id, pk=None):
    """Handles both editing and creating a cost allocation with associated transactions.

    If the pk is provided, it will edit, otherwise it will create a new allocation.
    """
    budget_period = get_object_or_404(BudgetPeriod, id=budget_id, user=request.user)

    TargetModel = CostAllocation if allocation_type == "cost" else IncomeAllocation
    TargetFormModel = (
        CostAllocationTransactionsForm
        if allocation_type == "cost"
        else IncomeAllocationTransactionsForm
    )
    transaction_field = (
        "cost_allocation" if allocation_type == "cost" else "income_allocation"
    )

    if pk:
        allocation = get_object_or_404(
            TargetModel, pk=pk, budget_period__user=request.user
        )
        title = "Edit Allocation"
        message = "Allocation updated!"
    else:
        allocation = None
        title = "Add Allocation"
        message = "Allocation saved!"

    if request.method == "POST":
        form = TargetFormModel(request.POST, instance=allocation)
        selected_ids = request.POST.getlist("transaction_ids")
        if form.is_valid():
            new_allocation = form.save(commit=False)
            new_allocation.budget_period = budget_period
            new_allocation.save()

            # Allocate ticked transactions
            Transaction.objects.filter(id__in=selected_ids, user=request.user).update(
                **{transaction_field: new_allocation}
            )
            # Unallocate any unticked
            Transaction.objects.filter(
                **{transaction_field: new_allocation}, user=request.user
            ).exclude(id__in=selected_ids).update(**{transaction_field: None})

            messages.success(request, message)
            return HttpResponseRedirect(reverse("detail", args=[budget_id]))

        else:
            messages.error(request, "Unable to save allocation.")
            return HttpResponseRedirect(reverse("detail", args=[budget_id]))

    else:
        transaction_ids = request.GET.getlist("transaction_ids")
        if not transaction_ids and allocation:
            transaction_ids = allocation.transactions.values_list(  # type: ignore
                "id", flat=True
            )
        selected_transactions = Transaction.objects.filter(
            user=request.user,
            id__in=transaction_ids,
        )
        form = TargetFormModel(instance=allocation, user=request.user)

    return render(
        request,
        "budget/forms/add_allocation_with_transactions_form.html",
        {
            "budget_id": budget_id,
            "form": form,
            "selected_transactions": selected_transactions,
            "title": title,
            "allocation_type": allocation_type,
        },
    )


@login_required
def move_cost_allocation(request, allocation_id, budget_id):
    """Moves a cost allocation to a neighbouring budget period"""
    allocation = get_object_or_404(
        CostAllocation.objects.select_related("budget_period"),
        pk=allocation_id,
        budget_period__user=request.user,
    )

    current_budget = allocation.budget_period.id
    budget_to_assign = get_object_or_404(BudgetPeriod, pk=budget_id, user=request.user)

    allocation.budget_period = budget_to_assign
    allocation.save()
    messages.success(request, "Allocation moved successfully.")

    return HttpResponseRedirect(reverse("detail", args=[current_budget]))


@login_required
def delete_allocation(request, allocation_type, pk, budget_id):
    TargetModel = CostAllocation if allocation_type == "cost" else IncomeAllocation

    allocation = get_object_or_404(TargetModel, pk=pk, budget_period__user=request.user)

    if request.method == "POST":
        allocation.delete()
        messages.success(request, "Allocation deleted")

    return HttpResponseRedirect(reverse("detail", args=[budget_id]))


@login_required
def delete_budget_period(request, pk):
    period = get_object_or_404(BudgetPeriod, pk=pk, user=request.user)

    if request.method == "POST":
        period.delete()
        messages.success(request, "Budget Period deleted")

    return HttpResponseRedirect(reverse("budgets-page"))


@login_required
def add_bucket(request, budget_id):
    if request.method == "POST":
        form = BucketForm(request.POST)
        if form.is_valid():
            new_bucket = form.save(commit=False)
            new_bucket.user = request.user
            new_bucket.save()
            messages.success(request, "Bucket added!")
            return HttpResponseRedirect(reverse("detail", args=[budget_id]))

        else:
            messages.error(request, "Unable to save bucket.")
            return HttpResponseRedirect(reverse("detail", args=[budget_id]))

    else:
        form = BucketForm(user=request.user)

    return render(
        request,
        "budget/forms/add_bucket_form.html",
        {
            "budget_id": budget_id,
            "form": form,
        },
    )


@login_required
def empty_bucket(request, budget_id, bucket_id):
    bucket = get_object_or_404(Bucket, pk=bucket_id, user=request.user)
    allocation = get_object_or_404(
        CostAllocation.objects.select_related("budget_period"),
        cost=bucket.cost_id,
        budget_period__user=request.user,
        budget_period_id=budget_id,
    )
    print(allocation)

    allocation.amount -= bucket.balance
    bucket.balance = 0

    bucket.save()
    allocation.save()

    return HttpResponseRedirect(reverse("detail", args=[budget_id]))


@login_required
def fill_bucket(request, budget_id, bucket_id):
    bucket = get_object_or_404(Bucket, pk=bucket_id, user=request.user)
    allocation = get_object_or_404(
        CostAllocation.objects.select_related("budget_period"),
        cost=bucket.cost_id,
        budget_period__user=request.user,
        budget_period_id=budget_id,
    )
    print(allocation)

    difference = allocation.remaining
    bucket.balance += difference
    allocation.amount += difference

    bucket.save()
    allocation.save()

    return HttpResponseRedirect(reverse("detail", args=[budget_id]))
