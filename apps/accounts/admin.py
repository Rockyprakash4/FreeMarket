from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "SkillSphere Profile"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_verified",
        "is_staff",
        "created_at",
    )
    list_filter = ("role", "is_verified", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("SkillSphere Role & Identity", {"fields": ("role", "is_verified", "phone", "location", "avatar")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("SkillSphere Role & Identity", {"fields": ("role", "is_verified", "email")}),
    )
    actions = ["verify_selected_users"]

    @admin.action(description="Verify selected users")
    def verify_selected_users(self, request, queryset):
        queryset.update(is_verified=True)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "headline",
        "experience_level",
        "hourly_rate",
        "verification_status",
        "ai_profile_score",
        "rating",
        "reviews_count",
    )
    list_filter = ("verification_status", "experience_level", "availability")
    search_fields = ("user__username", "user__email", "headline", "skills")
    actions = ["approve_verification", "reject_verification"]

    @admin.action(description="Approve verification for selected profiles")
    def approve_verification(self, request, queryset):
        for p in queryset:
            p.verification_status = Profile.VerificationStatus.VERIFIED
            p.user.is_verified = True
            p.user.save(update_fields=["is_verified"])
            p.save(update_fields=["verification_status"])

    @admin.action(description="Reject verification for selected profiles")
    def reject_verification(self, request, queryset):
        queryset.update(verification_status=Profile.VerificationStatus.REJECTED)
