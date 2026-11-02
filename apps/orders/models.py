from django.db import models
from django.conf import settings


class Order(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "In Progress"
        DELIVERED = "delivered", "Delivered & Under Review"
        COMPLETED = "completed", "Completed & Approved"
        DISPUTED = "disputed", "In Dispute"
        CANCELLED = "cancelled", "Cancelled"

    project = models.OneToOneField(
        "marketplace.Project",
        on_delete=models.CASCADE,
        related_name="order",
    )
    proposal = models.ForeignKey(
        "proposals.Proposal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_orders",
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="freelancer_orders",
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    freelancer_payout = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    delivery_notes = models.TextField(blank=True, default="")
    delivery_url = models.URLField(
        blank=True,
        null=True,
        help_text="Link to deliverables (GitHub PR, staging URL, live site, Drive folder)",
    )
    delivery_file = models.FileField(upload_to="deliveries/", blank=True, null=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} - {self.project.title}"
