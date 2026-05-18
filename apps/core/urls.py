from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("dashboard/<str:view_type>", views.dashboard, name="chosen-dashboard"),
    path("categories/", views.categories, name="categories-page"),
    path("set-preferences/", views.set_preferences, name="set-preferences"),
    path("add-category/", views.category_edit, name="add-category"),
    path("edit/<int:pk>", views.category_edit, name="edit-category"),
    path("delete/<int:pk>/", views.delete_category, name="delete-category"),
]
