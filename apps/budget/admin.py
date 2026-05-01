from django.contrib import admin
from apps.budget.models import BudgetPeriod, CostAllocation

# Register your models here.
admin.site.register(BudgetPeriod)

@admin.register(CostAllocation)
class CostAllocationAdmin(admin.ModelAdmin):
    readonly_fields = ('cost_name', 'cost_amount')
