from apps.cost import views
from django.urls import path

urlpatterns = [
    path('costs/', views.costs_list, name='costs-list')
]
