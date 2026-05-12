import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from apps.cost.models import Cost

from .forms import CostForm


# Create your views here.
def costs_page(request):
    return render(request, "cost/index.html")


@login_required
def costs_list(request):
    costs = Cost.objects.filter(user=request.user)

    context = {"costs": costs}
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
        if form.is_valid():
            cost_item = form.save(commit=False)
            cost_item.user = request.user
            cost_item.save()
            messages.success(request, message)
            return HttpResponseRedirect(f"/costs/?updated={cost_item.id}")

    else:
        form = CostForm(instance=cost, user=request.user)

    return render(
        request,
        "cost/forms/cost_form.html",
        {
            "form": form,
            "title": title,
        },
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
