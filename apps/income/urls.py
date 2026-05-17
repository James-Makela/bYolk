from django.urls import path

from apps.income import views

urlpatterns = [
    path("", views.incomes_list, name="incomes-page"),
    path("income/", views.income_edit, name="add-income"),
    path("edit/<int:pk>", views.income_edit, name="edit-income"),
    path("delete/<int:pk>/", views.delete_income, name="delete-income"),
    path("export", views.income_export, name="export-income"),
]
