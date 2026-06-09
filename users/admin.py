"""Админ-панель для пользователей и навыков."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Skill, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Расширенная админка пользователя с email-логином и навыками."""

    ordering = ("id",)
    list_display = ("id", "email", "name", "surname", "is_active", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "skills")
    search_fields = ("email", "name", "surname", "phone")
    filter_horizontal = ("skills", "groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Личная информация",
            {"fields": ("name", "surname", "avatar", "about", "phone", "github_url")},
        ),
        ("Навыки", {"fields": ("skills",)}),
        (
            "Права",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "name",
                    "surname",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    readonly_fields = ("date_joined", "last_login")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)
