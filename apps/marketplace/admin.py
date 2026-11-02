from django.contrib import admin
from .models import Category, Project


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "is_featured", "order")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_featured", "order")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "client",
        "category",
        "budget",
        "project_type",
        "status",
        "created_at",
    )
    list_filter = ("status", "project_type", "category")
    search_fields = ("title", "description", "client__username", "required_skills")
