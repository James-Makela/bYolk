from apps.transaction import views
from django.urls import path

urlpatterns = [
    path('', views.transaction_list, name='transactions-page')
]
