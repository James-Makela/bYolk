import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from apps.budget.services import sync_future_allocations
from apps.core.services import calculate_period_totals
from apps.cost.models import Cost
from apps.cost.services import save_cost

from .forms import CostForm


# Create your views here.
def costs_page(request):
    return render(request, "cost/index.html")


@login_required
def costs_list(request):
    raw_costs = Cost.objects.filter(user=request.user)

    active = []
    passed = []

    for cost in raw_costs:
        if cost.passed:
            passed.append(cost)
        else:
            active.append(cost)

    costs = active + passed

    totals = calculate_period_totals(raw_costs)

    context = {
        "costs": costs,
        "total_yearly": totals["yearly"],
        "total_monthly": totals["monthly"],
        "total_per_budget": totals["per_budget"],
        "total_per_week": totals["per_week"],
    }
    return render(request, "cost/index.html", context)


@login_required
def cost_edit(request, pk=None):
    """
    Creates or edits a Cost object, provides the cost form if request method is
    not POST.
    """
    if pk:
        cost = get_object_or_404(Cost, pk=pk, user=request.user)
        old_amount = cost.amount
        title = "Edit Cost"
        message = "Cost updated!"
    else:
        cost = None
        old_amount = None
        title = "Add Cost"
        message = "Cost saved!"

    if request.method == "POST":
        form = CostForm(request.POST, instance=cost, user=request.user)

        if form.is_valid():
            log_change = bool(request.POST.get("log_change"))

            with transaction.atomic():
                cost_item = save_cost(
                    cost, old_amount, form.cleaned_data, request.user, log_change
                )
                sync_future_allocations(cost_item)

            messages.success(request, message)
            return HttpResponseRedirect(f"/costs/?updated={cost_item.id}")

    else:
        form = CostForm(instance=cost, user=request.user)

    context = {
        "form": form,
        "title": title,
        "cost": cost,
    }

    return render(
        request,
        "cost/forms/cost_form.html",
        context,
    )


@login_required
def delete_cost(request, pk):
    cost = get_object_or_404(Cost, pk=pk, user=request.user)

    if request.method == "POST":
        cost.delete()
        messages.success(request, "Cost deleted")

    return HttpResponseRedirect("/costs/")


@login_required
def cost_export(request):
    costs = Cost.objects.filter(user=request.user)
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="costs.csv"'},
    )
    if not costs:
        return HttpResponseRedirect("/costs/")

    writer = csv.writer(response)
    writer.writerow(["name", "amount", "category", "start date", "keywords"])
    for cost in costs:
        writer.writerow(
            [
                cost.name,
                cost.amount,
                cost.category.name if cost.category else "",
                cost.start_date,
                cost.keywords,
            ]
        )
    return response
