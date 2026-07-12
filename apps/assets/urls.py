from django.urls import path

from apps.assets import views

urlpatterns = [
    path("", views.assets_list, name="assets-page"),
    path("add/", views.add_asset_choice, name="add-asset-choice"),
    path("add/property/", views.property_edit, name="add-property"),
    path("add/savings/", views.savings_edit, name="add-savings"),
    path("edit/property/<int:pk>", views.property_edit, name="edit-property"),
    path("edit/savings/<int:pk>", views.savings_edit, name="edit-savings"),
    path("delete/property/<int:pk>/", views.delete_property, name="delete-property"),
    path("delete/savings/<int:pk>/", views.delete_savings, name="delete-savings"),
]
