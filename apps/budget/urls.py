from django.urls import path

from apps.budget import views

urlpatterns = [
    path("", views.budgets_list, name="budgets-page"),
    path("generate/", views.start_next_budget, name="generate-budget"),
    path("<int:id>/", views.budget_detail, name="detail"),
    path("<int:id>/populate", views.populate_costs, name="populate-costs"),
    path(
        "edit/<int:pk>/<int:budget_id>",
        views.edit_allocation_with_transactions,
        name="edit-allocation",
    ),
    path(
        "allocation/<str:allocation_type>/<int:allocation_id>/picker/",
        views.get_allocation_picker,
        name="get_allocation_picker",
    ),
    path(
        "allocation/<str:allocation_type>/<int:allocation_id>/save/",
        views.save_allocations,
        name="save_allocations",
    ),
    path(
        "add-cost-allocation/<int:budget_id>",
        views.add_single_allocation,
        name="add-cost-allocation",
    ),
    path(
        "move-cost-allocation/<int:allocation_id>/<int:budget_id>",
        views.move_cost_allocation,
        name="move-cost-allocation",
    ),
    path(
        "create-allocation-with-transactions/<int:budget_id>",
        views.edit_allocation_with_transactions,
        name="allocation-with-transactions",
    ),
    path(
        "delete-allocation/<str:allocation_type>/<int:pk>/<int:budget_id>",
        views.delete_allocation,
        name="delete-allocation",
    ),
    path(
        "delete-budgetperiod/<int:pk>", views.delete_budget_period, name="delete-budget"
    ),
]
