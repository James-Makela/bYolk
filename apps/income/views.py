from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.income.models import Income


# Create your views here.
@login_required
def incomes_list(request):
    incomes = Income.objects.filter(user=request.user)

    context = {"incomes": incomes}
    return render(request, "income/index.html", context)


@login_required
def income_edit(request, pk=None):
    pass


@login_required
def delete_income(request, pk):
    pass


@login_required
def income_export(request):
    pass
