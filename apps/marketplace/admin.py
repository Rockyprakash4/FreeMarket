from django.contrib import admin
from .models import Category, Project, Service, SavedService


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
        "complexity",
        "project_type",
        "status",
        "created_at",
    )
    list_filter = ("status", "project_type", "complexity", "category")
    search_fields = ("title", "description", "client__username", "required_skills")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "freelancer",
        "category",
        "price",
        "delivery_time_days",
        "is_active",
        "views_count",
        "created_at",
    )
    list_filter = ("is_active", "category")
    search_fields = ("title", "description", "freelancer__username", "technologies")


@admin.register(SavedService)
class SavedServiceAdmin(admin.ModelAdmin):
    list_display = ("user", "service", "created_at")
    search_fields = ("user__username", "service__title")
