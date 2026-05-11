from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    # path('', views.index, name='index'),
    path("categories/", views.categories, name="categories-page"),
    path("add-category/", views.create_category, name="add-category"),
    path("delete/<int:pk>/", views.delete_category, name="delete-category"),
    path("set-preferences/", views.set_preferences, name="set-preferences"),
]
