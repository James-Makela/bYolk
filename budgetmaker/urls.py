from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("apps.core.urls")),
    path("costs/", include("apps.cost.urls")),
    path("transactions/", include("apps.transaction.urls")),
    path("budgets/", include("apps.budget.urls")),
    path("incomes/", include("apps.income.urls")),
]
