from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.transaction.filters import TransactionFilter
from apps.transaction.models import Transaction


# Create your views here.
def transactions_page(request):
    return render(request, 'cost/index.html')


@login_required
def transaction_list(request):
    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user)
    )
    context = {'filter': transaction_filter}
    return render(request, 'transaction/index.html', context)
