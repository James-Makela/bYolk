from django.urls import path

from apps.cost import views

urlpatterns = [
    # path('', views.index, name='index'),
    path("", views.costs_list, name="costs-page"),
    path("cost/", views.cost_edit, name="add-cost"),
    path("edit/<int:pk>", views.cost_edit, name="edit-cost"),
    path("delete/<int:pk>/", views.delete_cost, name="delete-cost"),
    path("export", views.cost_export, name="export-costs"),
]
