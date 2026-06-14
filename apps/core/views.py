from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from apps.cost.models import Cost
from apps.income.models import Income

from .forms import CategoryForm, InitialUserPreferencesForm
from .models import Category
from .services import get_cost_graph_data


# Create your views here.
@login_required
def dashboard(request, view_type="categories"):
    charts = []
    costs = Cost.objects.filter(user=request.user)
    incomes = Income.objects.filter(user=request.user)
    categories = Category.objects.filter(user=request.user)

    if view_type == "costs":
        for cost in costs:
            graph_data = get_cost_graph_data(request.user, cost=cost)
            if graph_data:
                charts.append(graph_data)

    if view_type == "categories":
        for category in categories:
            graph_data = get_cost_graph_data(request.user, category=category)
            if graph_data:
                charts.append(graph_data)

    # TODO: This is duplicated in costs view - needs to be moved to the Cost class
    total_costs_per_year = 0
    total_costs_per_budget = 0
    total_costs_per_week = 0
    for cost in costs:
        total_costs_per_year += cost.cost_per_year
        total_costs_per_budget += cost.cost_per_budget_period
        total_costs_per_week += cost.cost_per_week

    total_income_per_year = 0
    total_income_per_budget = 0
    total_income_per_week = 0
    for income in incomes:
        total_income_per_year += income.income_per_year
        total_income_per_budget += income.income_per_budget_period
        total_income_per_week += income.income_per_week

    context = {
        "charts": charts,
        "view_type": view_type,
        "total_yearly": total_costs_per_year,
        "total_monthly": total_costs_per_year / 12,
        "total_per_budget": total_costs_per_budget,
        "total_per_week": total_costs_per_week,
        "total_income_yearly": total_income_per_year,
        "total_income_monthly": total_income_per_year / 12,
        "total_income_per_budget": total_income_per_budget,
        "total_income_per_week": total_income_per_week,
        "total_savings_yearly": total_income_per_year - total_costs_per_year,
        "total_savings_monthly": (total_income_per_year - total_costs_per_year) / 12,
        "total_savings_per_budget": total_income_per_budget - total_costs_per_budget,
        "total_savings_per_week": total_income_per_week - total_costs_per_week,
    }
    return render(request, "dashboard.html", context)


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
            return HttpResponseRedirect("/categories/")

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

    return HttpResponseRedirect("/categories/")


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
            return HttpResponseRedirect("/categories/")

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
