from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("order", "reviewer", "reviewee", "rating", "is_reported", "is_moderated", "created_at")
    list_filter = ("rating", "is_reported", "is_moderated")
    search_fields = (
        "order__id",
        "reviewer__username",
        "reviewee__username",
        "comment",
    )
    actions = ["unflag_and_approve", "remove_reported_review"]

    @admin.action(description="Unflag and approve selected reviews")
    def unflag_and_approve(self, request, queryset):
        queryset.update(is_reported=False, is_moderated=True)

    @admin.action(description="Remove reported reviews")
    def remove_reported_review(self, request, queryset):
        queryset.delete()
