from apps.budget import views
from django.urls import path

urlpatterns = [
    path('', views.budgets_list, name='budgets-page')
]
