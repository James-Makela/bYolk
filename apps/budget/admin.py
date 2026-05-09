from django.contrib import admin

from apps.budget.models import BudgetPeriod, CostAllocation, IncomeAllocation

# Register your models here.
admin.site.register(BudgetPeriod)
admin.site.register(CostAllocation)
admin.site.register(IncomeAllocation)
