from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from apps.transaction.filters import TransactionFilter
from apps.transaction.models import Transaction

from .services import process_transaction_upload



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

@login_required
def upload_csv(request):
    if request.method == "POST" and request.FILES.get('csv_file'):
        try:
            created_count = process_transaction_upload(request.user, request.FILES['csv_file'])
            messages.success(request, f"Successfully uploaded {len(created_count)} items.")
        except Exception as e:
            messages.error(request, f"Upload failed: {str(e)}")

    return HttpResponseRedirect('/transactions/')
