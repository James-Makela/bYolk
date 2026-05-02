from apps.cost import views
from django.urls import path

urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.costs_list, name='costs-page'),
    path('add-cost/', views.get_cost, name='add-cost'),
    path('delete/<int:pk>/', views.delete_cost, name='delete-cost'),
]
