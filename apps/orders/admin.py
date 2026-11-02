from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "client",
        "freelancer",
        "total_amount",
        "platform_fee",
        "freelancer_payout",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "project__title",
        "client__username",
        "freelancer__username",
    )
