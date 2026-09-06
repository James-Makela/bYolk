from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.db.models import BooleanField, Case, Sum, Value, When
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.assets.models import SavingsAccount
from apps.budget.models import Bucket, BudgetPeriod, CostAllocation, IncomeAllocation
from apps.core.forms import InitialUserPreferencesForm
from apps.transaction.models import Transaction

from .forms import (
    BucketEmptyFormSet,
    BucketForm,
    CostAllocationForm,
    CostAllocationTransactionsForm,
    IncomeAllocationTransactionsForm,
)
from .services import (
    generate_next_budget_period,
    get_running_savings,
    populate_from_costs,
)


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
        .order_by("-start_date")
        .with_transaction_stats()
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
        BudgetPeriod.objects.filter(user=request.user),
        pk=id,
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
    ungrouped_allocations_unsorted = allocations.exclude(
        name__in=[g["name"] for g in grouped_allocations]
    )
    ungrouped_allocations = sorted(
        ungrouped_allocations_unsorted, key=lambda x: x.expected_amount
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

    primary_savings = SavingsAccount.objects.filter(
        user=request.user, is_primary=True
    ).first()

    if not complete or not primary_savings:
        theoretical_predicted_savings, actual_predicted_savings = get_running_savings(
            request.user, budget
        )
    else:
        theoretical_predicted_savings = 0
        actual_predicted_savings = 0

    context = {
        "budget": budget,
        "budget_id": budget.id,
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
        "savings": primary_savings,
        "theoretical_predicted_savings": theoretical_predicted_savings,
        "actual_predicted_savings": actual_predicted_savings,
        **get_category_pie_context(request, id),
        "forecast": False,
        "next_forecast_value": True,
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
        "budget/partials/_transaction_picker_modal.html",
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

            allocation.expected_amount = total_sum
            allocation.amount = total_sum
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
            new_allocation.amount = -new_allocation.amount
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
        allocation.expected_amount = -allocation.expected_amount
        allocation.amount = -allocation.amount
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
            if TargetModel == CostAllocation:
                new_allocation.amount = -new_allocation.amount
                new_allocation.expected_amount = -new_allocation.expected_amount
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

    # Check if there are associated costs with the allocation
    if allocation.transactions.all().exists():
        messages.error(request, "Unable to move allocation with transactions")

        return HttpResponseRedirect(reverse("detail", args=[current_budget]))

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
    budget = get_object_or_404(BudgetPeriod, pk=budget_id, user=request.user)

    allocations = CostAllocation.objects.filter(
        budget_period__user=request.user,
        budget_period_id=budget_id,
    )

    formset = BucketEmptyFormSet(queryset=allocations)

    return render(
        request,
        "budget/partials/_allocation_picker_modal.html",
        {
            "bucket": bucket,
            "budget": budget,
            "formset": formset,
        },
    )


@login_required
def allocate_from_bucket(request, budget_id, bucket_id):
    bucket = get_object_or_404(Bucket, pk=bucket_id, user=request.user)
    budget = get_object_or_404(BudgetPeriod, pk=budget_id, user=request.user)

    if request.method != "POST":
        return HttpResponse(status=405)

    allocations = CostAllocation.objects.filter(
        budget_period__user=request.user,
        budget_period_id=budget_id,
    )

    formset = BucketEmptyFormSet(request.POST, queryset=allocations)

    if not formset.is_valid():
        return render(
            request,
            "budget/partials/_allocation_picker_modal.html",
            {"bucket": bucket, "budget": budget, "formset": formset},
        )

    selected_forms = [form for form in formset if form.cleaned_data.get("selected")]
    total = sum(form.cleaned_data["amount"] for form in selected_forms)

    # TODO: Add/remove note as required when allocating from a bucket
    with db_transaction.atomic():
        bucket.balance -= total
        bucket.save()
        for form in selected_forms:
            form.instance.amount -= form.cleaned_data["amount"]
            form.instance.save()

    response = HttpResponse("Saved")
    response["HX-Refresh"] = "true"

    return response


@login_required
def fill_bucket(request, budget_id, bucket_id):
    bucket = get_object_or_404(Bucket, pk=bucket_id, user=request.user)

    allocations = CostAllocation.objects.filter(
        cost=bucket.cost_id,
        budget_period__user=request.user,
        budget_period_id=budget_id,
    )

    for allocation in allocations:
        difference = allocation.remaining
        bucket.balance += difference
        allocation.amount += difference
        allocation.note = "Remainder sent to bucket"
        allocation.save()

    bucket.save()

    return HttpResponseRedirect(reverse("detail", args=[budget_id]))


@login_required
def category_pie_chart(request, budget_id):
    forecast = request.GET.get("forecast") == "true"
    chart_context = get_category_pie_context(request, budget_id, forecast=forecast)
    chart_html = render_to_string(
        "partials/_category_pie_chart.html", chart_context, request=request
    )
    button_context = {
        "budget_id": budget_id,
        "forecast": forecast,
        "next_forecast_value": not forecast,
        "hx_oob": True,
    }
    button_html = render_to_string(
        "partials/_forecast_toggle_button.html", button_context, request=request
    )
    return HttpResponse(chart_html + button_html)


@login_required
def get_category_pie_context(request, budget_id, forecast=False):
    budget = get_object_or_404(
        BudgetPeriod.objects.filter(user=request.user),
        pk=budget_id,
    )

    if forecast:
        category_totals = (
            CostAllocation.objects.filter(budget_period=budget)
            .values("category__name", "category__color")
            .annotate(total=Coalesce(Sum("expected_amount"), Decimal(0.0)))
            .order_by("total")
        )
    else:
        category_totals = (
            CostAllocation.objects.filter(budget_period=budget)
            .values("category__name", "category__color")
            .annotate(total=Coalesce(Sum("transactions__amount"), Decimal(0.0)))
            .order_by("total")
            .exclude(total=0)
        )

    pie_category_labels = []
    pie_category_series = []
    pie_category_colors = []

    if len(category_totals) > 0:
        print(category_totals[0])

    if forecast:
        for item in category_totals:
            pie_category_labels.append(item["category__name"] or "Uncategorized")
            pie_category_series.append(abs(float(item["total"])))
            pie_category_colors.append(item["category__color"] or "#999999")
    else:
        for item in category_totals:
            pie_category_labels.append(item["category__name"] or "Uncategorized")
            pie_category_series.append(abs(float(item["total"])))
            pie_category_colors.append(item["category__color"] or "#999999")

    return {
        "pie_category_labels": pie_category_labels,
        "pie_category_series": pie_category_series,
        "pie_category_colors": pie_category_colors,
        "budget": budget,
    }
