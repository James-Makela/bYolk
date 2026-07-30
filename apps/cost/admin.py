from django.contrib import admin

from apps.cost.models import Cost, CostChange

# Register your models here.
admin.site.register(Cost)
admin.site.register(CostChange)
