from django.contrib import admin
from .models import Proposal


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "freelancer",
        "proposed_price",
        "estimated_delivery_days",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("project__title", "freelancer__username", "cover_letter")
