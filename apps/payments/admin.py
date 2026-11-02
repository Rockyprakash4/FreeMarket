from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "order",
        "payer",
        "amount",
        "platform_fee",
        "net_payout",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("transaction_id", "payer__username", "order__project__title")
