from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.budget.models import IncomeAllocation
from apps.income.models import Income, IncomeChange

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
        old_amount = income.amount if income else None
        if form.is_valid():
            new_amount = form.cleaned_data["amount"]
            log_change = request.POST.get("log_change")
            income_item = form.save(commit=False)
            income_item.user = request.user

            # If the user wants to log this change, we create a change object
            if log_change and old_amount != new_amount:
                IncomeChange.objects.update_or_create(
                    income=income,
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
                IncomeChange.objects.filter(
                    income=income, date_changed=timezone.now().date()
                ).delete()
            income_item.save()

            IncomeAllocation.objects.filter(
                income=income_item,
                expected_date__gt=timezone.now().date(),
            ).update(
                amount=form.cleaned_data["amount"],
                name=form.cleaned_data["name"],
            )

            messages.success(request, message)
            return HttpResponseRedirect(f"/incomes/?updated={income_item.id}")

    else:
        form = IncomeForm(instance=income, user=request.user)

    context = {
        "form": form,
        "title": title,
        "income": income,
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
