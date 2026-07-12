from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from apps.assets.models import PropertyAsset, SavingsAccount

from .forms import PropertyForm, SavingsForm


# Create your views here.
@login_required
def assets_list(request):
    properties = PropertyAsset.objects.filter(user=request.user)
    savings = SavingsAccount.objects.filter(user=request.user)

    context = {
        "properties": properties,
        "savings": savings,
    }
    return render(request, "assets/index.html", context)


@login_required
def add_asset_choice(request):
    return render(request, "assets/partials/_add_asset_choice.html")


@login_required
def property_edit(request, pk=None):
    if pk:
        property = get_object_or_404(PropertyAsset, pk=pk, user=request.user)
        title = "Edit Property Asset"
        message = "Property updated!"
    else:
        property = None
        title = "Add Property Asset"
        message = "Property added!"

    if request.method == "POST":
        form = PropertyForm(request.POST, instance=property)
        if form.is_valid():
            property_item = form.save(commit=False)
            property_item.user = request.user
            property_item.save()

            messages.success(request, message)
            return HttpResponseRedirect(f"/assets/?updated={property_item.id}")

    else:
        form = PropertyForm(instance=property)

    context = {
        "form": form,
        "title": title,
        "property": property,
    }

    return render(
        request,
        "assets/forms/property_form.html",
        context,
    )


@login_required
def savings_edit(request, pk=None):
    if pk:
        savings_account = get_object_or_404(SavingsAccount, pk=pk, user=request.user)
        title = "Edit Savings Account"
        message = "Savings account updated!"
    else:
        savings_account = None
        title = "Add Savings Account"
        message = "Savings account added!"

    if request.method == "POST":
        form = SavingsForm(request.POST, instance=savings_account)
        if form.is_valid():
            savings_account_item = form.save(commit=False)
            savings_account_item.user = request.user
            savings_account_item.save()

            messages.success(request, message)
            return HttpResponseRedirect(f"/assets/?updated={savings_account_item.id}")

    else:
        form = SavingsForm(instance=savings_account)

    context = {
        "form": form,
        "title": title,
        "savings_account": savings_account,
    }

    return render(
        request,
        "assets/forms/savings_form.html",
        context,
    )


@login_required
def delete_property(request, pk):
    property = get_object_or_404(PropertyAsset, pk=pk, user=request.user)

    if request.method == "POST":
        property.delete()
        messages.success(request, "Property deleted")

    return HttpResponseRedirect("/assets/")


@login_required
def delete_savings(request, pk):
    property = get_object_or_404(SavingsAccount, pk=pk, user=request.user)

    if request.method == "POST":
        property.delete()
        messages.success(request, "Savings account deleted")

    return HttpResponseRedirect("/assets/")
