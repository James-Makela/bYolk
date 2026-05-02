from apps.core import views
from django.urls import path

urlpatterns = [
    # path('', views.index, name='index'),
    path('categories/', views.categories, name='categories-page'),
    path('add-category/', views.create_category, name='add-category'),
    path('delete/<int:pk>/', views.delete_category, name='delete-category'),
]
