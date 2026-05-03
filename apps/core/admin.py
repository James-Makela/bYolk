from django.contrib import admin

from apps.core.models import Category, User, UserPreferences

# Register your models here.
admin.site.register(User)
admin.site.register(Category)
admin.site.register(UserPreferences)
