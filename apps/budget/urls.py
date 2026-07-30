from django.urls import path

from apps.budget import views

urlpatterns = [
    # Budget urls
    path("", views.budgets_list, name="budgets-page"),
    path("generate/", views.start_next_budget, name="generate-budget"),
    path("<int:id>/", views.budget_detail, name="detail"),
    path("populate/<int:id>/", views.populate_costs, name="populate-costs"),
    path("delete/<int:pk>", views.delete_budget_period, name="delete-budget"),
    # Allocation urls
    path(
        "allocation/edit/<str:allocation_type>/<int:pk>/<int:budget_id>",
        views.edit_allocation_with_transactions,
        name="edit-allocation",
    ),
    path(
        "allocation/picker/<str:allocation_type>/<int:allocation_id>/",
        views.get_allocation_picker,
        name="get-allocation-picker",
    ),
    path(
        "allocation/save/<str:allocation_type>/<int:allocation_id>/",
        views.save_allocations,
        name="save-allocations",
    ),
    path(
        "allocation/add-cost/<int:budget_id>",
        views.add_single_allocation,
        name="add-cost-allocation",
    ),
    path(
        "allocation/move-cost/<int:allocation_id>/<int:budget_id>",
        views.move_cost_allocation,
        name="move-cost-allocation",
    ),
    path(
        "allocation/add-with-transactions/<str:allocation_type>/<int:budget_id>",
        views.edit_allocation_with_transactions,
        name="allocation-with-transactions",
    ),
    path(
        "allocation/delete/<str:allocation_type>/<int:pk>/<int:budget_id>",
        views.delete_allocation,
        name="delete-allocation",
    ),
    # Bucket urls
    path(
        "bucket/add/<int:budget_id>",
        views.add_bucket,
        name="add-bucket",
    ),
    path(
        "bucket/empty/<int:budget_id>/<int:bucket_id>",
        views.empty_bucket,
        name="empty-bucket",
    ),
    path(
        "bucket/fill/<int:budget_id>/<int:bucket_id>",
        views.fill_bucket,
        name="fill-bucket",
    ),
]
