from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.core.models import Category, User, UserPreferences


# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ["email", "is_staff", "is_active"]
    ordering = ["email"]
    fieldsets = (  # type: ignore
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )


admin.site.register(Category)
admin.site.register(UserPreferences)
