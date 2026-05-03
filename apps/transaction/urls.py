from django.urls import path

from apps.transaction import views

urlpatterns = [
    path("", views.transaction_list, name="transactions-page"),
    path("upload-csv/", views.upload_csv, name="upload-csv"),
]
