import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required, login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.budget.models import CostAllocation

from .forms import CategoryForm, CustomUserCreationForm, InitialUserPreferencesForm
from .models import Category


# Create your views here.
@login_required
def dashboard(request):
    today = timezone.now().date()
    groceries_allocations = CostAllocation.objects.filter(
        budget_period__user=request.user,
        name="Groceries",
        budget_period__end_date__lte=today,
    ).order_by("budget_period__end_date")

    petrol_allocations = CostAllocation.objects.filter(
        budget_period__user=request.user,
        name="Petrol",
        budget_period__end_date__lte=today,
    ).order_by("budget_period__end_date")

    groceries = {
        "title": "Groceries",
        "chart_id": "groceries",
        "dates": json.dumps(
            [
                a.budget_period.start_date.strftime("%d, %b %Y")
                for a in groceries_allocations
            ]
        ),
        "amounts": json.dumps([float(a.amount) for a in groceries_allocations]),
        "color": groceries_allocations[0].cost.category.color,
    }
    petrol = {
        "title": "Petrol",
        "chart_id": "petrol",
        "dates": json.dumps(
            [
                a.budget_period.start_date.strftime("%d, %b %Y")
                for a in petrol_allocations
            ]
        ),
        "amounts": json.dumps([float(a.amount) for a in petrol_allocations]),
        "color": petrol_allocations[0].cost.category.color,
    }
    context = {
        "groceries": groceries,
        "petrol": petrol,
    }
    return render(request, "dashboard.html", context)


@login_not_required
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in immediately after signing up
            return redirect("home")  # Redirect to your main page
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def categories(request):
    categories = Category.objects.filter(user=request.user)
    return render(request, "category/index.html", {"categories": categories})


@login_required
def create_category(request):
    if request.method == "POST":
        # Create a form instance and populate it with data from the rrequest
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, "Category added!")
            return HttpResponseRedirect("/core/categories/")

    # If a GET or any other method create a blank form
    else:
        form = CategoryForm()

    return render(request, "category/forms/add_category_form.html", {"form": form})


@login_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)

    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted")

    return HttpResponseRedirect("/core/categories/")


@login_required
def set_preferences(request):
    if request.method == "POST":
        form = InitialUserPreferencesForm(request.POST)
        if form.is_valid():
            preferences = form.save(commit=False)
            preferences.user = request.user
            preferences.save()
            messages.success(
                request, "Preferences saved, you can now create your first budget"
            )
            return HttpResponseRedirect("/budgets/")


@login_required
def category_edit(request, pk=None):
    if pk:
        category = get_object_or_404(Category, pk=pk, user=request.user)
        title = "Edit Category"
        message = "Category updated!"
    else:
        category = None
        title = "Add Category"
        message = "Category saved!"

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            new_category = form.save(commit=False)
            new_category.user = request.user
            new_category.save()
            messages.success(request, message)
            return HttpResponseRedirect("/core/categories/")

    else:
        form = CategoryForm(instance=category)

    return render(
        request,
        "category/forms/add_category_form.html",
        {
            "form": form,
            "title": title,
        },
    )
