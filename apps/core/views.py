from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render

from apps.cost.models import Cost
from apps.income.models import Income

from .forms import CategoryForm, InitialUserPreferencesForm
from .models import Category
from .services import calculate_period_totals, get_graph_data, get_total_spend_data


# Create your views here.
@login_required
def dashboard(request, view_type="categories"):
    time_period = request.session["graph_period"]
    if not time_period:
        time_period = 365
    charts = []
    income_graph = []
    costs = Cost.objects.filter(user=request.user)
    incomes = Income.objects.filter(user=request.user)
    categories = Category.objects.filter(user=request.user)

    if view_type == "costs":
        for cost in costs:
            graph_data = get_graph_data(
                request.user, cost=cost, time_period=time_period
            )
            if graph_data:
                charts.append(graph_data)

    if view_type == "categories":
        for category in categories:
            graph_data = get_graph_data(
                request.user, category=category, time_period=time_period
            )
            if graph_data:
                charts.append(graph_data)

    cost_totals = calculate_period_totals(costs)
    income_totals = calculate_period_totals(incomes)

    for income in incomes:
        income_data = get_graph_data(
            request.user, income=income, time_period=time_period
        )
        if income_data:
            income_graph.append(income_data)

    income_dates = income_graph[0]["dates"]
    income_amounts = []
    income_titles = []
    for income in income_graph:
        income_amounts.append(income["amounts"])
        income_titles.append(income["title"])

    total_spend_amounts = get_total_spend_data(request.user, time_period)

    context = {
        # Cost Graphs
        "charts": charts,
        "view_type": view_type,
        # Income graph
        "income_dates": income_dates,
        "income_titles": income_titles,
        "income_amounts": income_amounts,
        "total_spend_amounts": total_spend_amounts,
        # Costs
        "total_yearly": cost_totals["yearly"],
        "total_monthly": cost_totals["yearly"] / 12,
        "total_per_budget": cost_totals["per_budget"],
        "total_per_week": cost_totals["per_week"],
        # Income
        "total_income_yearly": income_totals["yearly"],
        "total_income_monthly": income_totals["yearly"] / 12,
        "total_income_per_budget": income_totals["per_budget"],
        "total_income_per_week": income_totals["per_week"],
        # Savings
        "total_savings_yearly": income_totals["yearly"] - cost_totals["yearly"],
        "total_savings_monthly": (income_totals["yearly"] - cost_totals["yearly"]) / 12,
        "total_savings_per_budget": income_totals["per_budget"]
        - cost_totals["per_budget"],
        "total_savings_per_week": income_totals["per_week"] - cost_totals["per_week"],
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


@login_required
def theme_select(request):
    request.session["theme"] = request.POST.get("theme")

    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def toggle_privacy_mode(request):
    current_state = request.session.get("privacy_mode", False)
    request.session["privacy_mode"] = not current_state

    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def select_graph_period(request, days):
    request.session["graph_period"] = days

    return redirect(request.META.get("HTTP_REFERER", "/"))
