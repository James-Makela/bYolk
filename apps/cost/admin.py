from django.contrib import admin
from apps.cost.models import Category, Cost


# Register your models here.
admin.site.register(Cost)
admin.site.register(Category)
