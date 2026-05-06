from django.urls import path

from apps.budget import views

urlpatterns = [
    path("", views.budgets_list, name="budgets-page"),
    path("generate/", views.start_next_budget, name="generate-budget"),
    path("<int:id>/", views.budget_detail, name="detail"),
    path("<int:id>/populate", views.populate_costs, name="populate-costs"),
    path(
        "allocation/<int:allocation_id>/picker/",
        views.get_allocation_picker,
        name="get_allocation_picker",
    ),
    path(
        "allocation/<int:allocation_id>/save/",
        views.save_allocations,
        name="save_allocations",
    ),
]
