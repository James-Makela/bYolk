from django.urls import path

from apps.transaction import views

urlpatterns = [
    path("", views.transaction_list, name="transactions-page"),
    path("upload-csv-ing/", views.upload_csv_ing, name="upload-csv-ing"),
]
