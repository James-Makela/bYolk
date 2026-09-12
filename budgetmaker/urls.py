from pwa import views as pwa_views

from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("manifest.json", login_not_required(pwa_views.manifest), name="manifest"),
    path(
        "serviceworker.js",
        login_not_required(pwa_views.service_worker),
        name="service_worker",
    ),
    path("offline/", login_not_required(pwa_views.offline), name="offline"),
    path("", include("apps.core.urls")),
    path("costs/", include("apps.cost.urls")),
    path("transactions/", include("apps.transaction.urls")),
    path("budgets/", include("apps.budget.urls")),
    path("incomes/", include("apps.income.urls")),
    path("assets/", include("apps.assets.urls")),
]
