from apps.budget import views
from django.urls import path

urlpatterns = [
    path('', views.budgets_list, name='budgets-page'),
    path('generate/', views.start_next_budget, name='generate-budget'),
    path("<int:budget_id>/", views.budget_detail, name="detail"),
    path("<int:budget_id>/populate", views.populate_costs, name="populate-costs"),
]
