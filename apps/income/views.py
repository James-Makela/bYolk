from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from apps.income.models import Income

from .forms import IncomeForm


# Create your views here.
@login_required
def incomes_list(request):
    incomes = Income.objects.filter(user=request.user)

    context = {"incomes": incomes}
    return render(request, "income/index.html", context)


@login_required
def income_edit(request, pk=None):
    if pk:
        income = get_object_or_404(Income, pk=pk, user=request.user)
        title = "Edit Income"
        message = "Income updated!"
    else:
        income = None
        title = "Add Income"
        message = "Income added!"

    if request.method == "POST":
        form = IncomeForm(request.POST, instance=income, user=request.user)
        if form.is_valid():
            income_item = form.save(commit=False)
            income_item.user = request.user
            income_item.save()
            messages.success(request, message)
            return HttpResponseRedirect(f"/incomes/?updated={income_item.id}")

    else:
        form = IncomeForm(instance=income, user=request.user)

    context = {
        "form": form,
        "title": title,
    }

    return render(
        request,
        "income/forms/income_form.html",
        context,
    )


@login_required
def delete_income(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)

    if request.method == "POST":
        income.delete()
        messages.success(request, "Income deleted")

    return HttpResponseRedirect("/incomes/")
