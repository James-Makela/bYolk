from django.contrib import admin

from apps.budget.models import Bucket, BudgetPeriod, CostAllocation, IncomeAllocation

# Register your models here.
admin.site.register(BudgetPeriod)
admin.site.register(CostAllocation)
admin.site.register(IncomeAllocation)
admin.site.register(Bucket)
