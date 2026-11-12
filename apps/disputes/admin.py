from django.contrib import admin
from .models import Dispute


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "raised_by",
        "reason",
        "status",
        "resolved_by",
        "resolved_at",
        "created_at",
    )
    list_filter = ("status", "reason")
    search_fields = ("order__id", "raised_by__username", "description", "resolution_notes")
