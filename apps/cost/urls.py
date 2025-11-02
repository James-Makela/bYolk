from apps.cost import views
from django.urls import path

urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.costs_list, name='costs-page')
]
