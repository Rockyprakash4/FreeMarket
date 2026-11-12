from django.contrib import admin
from .models import Order, Milestone


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "service",
        "client",
        "freelancer",
        "total_amount",
        "platform_fee",
        "freelancer_payout",
        "status",
        "revision_count",
        "created_at",
    )
    list_filter = ("status", "revision_requested")
    search_fields = (
        "project__title",
        "service__title",
        "client__username",
        "freelancer__username",
    )
    inlines = [MilestoneInline]


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "order_num",
        "title",
        "amount",
        "due_date",
        "status",
        "submitted_at",
        "approved_at",
    )
    list_filter = ("status",)
    search_fields = ("title", "description", "order__id")
