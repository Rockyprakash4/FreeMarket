from django.db import models
from django.conf import settings
import uuid


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Payment"
        HELD_IN_ESCROW = "held_in_escrow", "Held in Safe Escrow"
        RELEASED = "released", "Released to Freelancer"
        REFUNDED = "refunded", "Refunded to Client"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments_made",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total amount in USD")
    platform_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, help_text="Platform commission (10%)"
    )
    net_payout = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, help_text="Amount disbursed to freelancer"
    )
    currency = models.CharField(max_length=10, default="USD")
    payment_method = models.CharField(
        max_length=50, default="DevMarket Safe Mock Escrow"
    )
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.HELD_IN_ESCROW
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment #{self.transaction_id} (${self.amount}) - {self.status}"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
