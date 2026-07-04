import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.budget.models import CostAllocation
from apps.core.services import calculate_period_totals
from apps.cost.models import Cost, CostChange

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

    totals = calculate_period_totals(costs)

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
    if pk:
        cost = get_object_or_404(Cost, pk=pk, user=request.user)
        title = "Edit Cost"
        message = "Cost updated!"
    else:
        cost = None
        title = "Add Cost"
        message = "Cost saved!"

    if request.method == "POST":
        form = CostForm(request.POST, instance=cost, user=request.user)
        old_amount = cost.amount if cost else None
        if form.is_valid():
            new_amount = form.cleaned_data["amount"]
            log_change = request.POST.get("log_change")
            cost_item = form.save(commit=False)
            cost_item.user = request.user

            # If the user wants to log this change, we create a change object
            if log_change and old_amount != new_amount:
                CostChange.objects.update_or_create(
                    cost=cost,
                    date_changed=timezone.now().date(),
                    defaults={
                        "new_amount": new_amount,
                    },
                    create_defaults={
                        "new_amount": new_amount,
                        "previous_amount": old_amount,
                    },
                )
            elif old_amount == new_amount:
                CostChange.objects.filter(
                    cost=cost, date_changed=timezone.now().date()
                ).delete()
            cost_item.save()

            CostAllocation.objects.filter(
                cost=cost_item,
                expected_date__gt=timezone.now().date(),
            ).update(amount=-form.cleaned_data["amount"])

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
                cost.category.name,
                cost.start_date,
                cost.keywords,
            ]
        )
    return response
