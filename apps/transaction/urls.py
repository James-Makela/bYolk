from apps.transaction import views
from django.urls import path

urlpatterns = [
    path('', views.transaction_list, name='transactions-page'),
    path('upload-csv/', views.upload_csv, name='upload-csv'),
]
