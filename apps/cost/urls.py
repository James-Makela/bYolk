from apps.cost import views
from django.urls import path

urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.costs_list, name='costs-page'),
    path('add-cost/', views.cost_edit, name='add-cost'),
    path('edit/<int:pk>', views.cost_edit, name='edit-cost'),
    path('delete/<int:pk>/', views.delete_cost, name='delete-cost'),
]
