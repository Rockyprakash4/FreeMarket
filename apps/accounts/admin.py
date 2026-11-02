from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Freelancer Profile"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "created_at",
    )
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("DevMarket Details", {"fields": ("role", "phone", "location", "avatar")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("DevMarket Details", {"fields": ("role", "email")}),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "headline",
        "experience_level",
        "hourly_rate",
        "availability",
        "rating",
        "reviews_count",
    )
    list_filter = ("experience_level", "availability")
    search_fields = ("user__username", "user__email", "headline", "skills")
