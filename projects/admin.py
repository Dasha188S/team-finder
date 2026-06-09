"""Админ-панель для проектов."""
from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "description", "owner__email")
    autocomplete_fields = ("owner",)
    filter_horizontal = ("participants",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
