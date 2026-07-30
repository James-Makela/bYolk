from django.contrib import admin

from apps.assets.models import PropertyAsset, SavingsAccount

# Register your models here.
admin.site.register(PropertyAsset)
admin.site.register(SavingsAccount)
