from django.db import models
from django.conf import settings


class Order(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "In Progress"
        DELIVERED = "delivered", "Delivered & Under Review"
        IN_REVISION = "in_revision", "Revision Requested"
        COMPLETED = "completed", "Completed & Approved"
        DISPUTED = "disputed", "In Dispute"
        CANCELLED = "cancelled", "Cancelled"

    project = models.ForeignKey(
        "marketplace.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    service = models.ForeignKey(
        "marketplace.Service",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
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

    # Revision Management
    revision_requested = models.BooleanField(default=False)
    revision_notes = models.TextField(blank=True, default="")
    revision_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        title = self.project.title if self.project else (self.service.title if self.service else "Custom Order")
        return f"Order #{self.id} - {title}"

    @property
    def title(self):
        if self.project:
            return self.project.title
        elif self.service:
            return self.service.title
        return f"Order #{self.id}"


class Milestone(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Work"
        IN_PROGRESS = "in_progress", "In Progress"
        SUBMITTED = "submitted", "Submitted for Review"
        IN_REVISION = "in_revision", "Revision Requested"
        APPROVED = "approved", "Approved & Completed"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="milestones",
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    order_num = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    submission_notes = models.TextField(blank=True, default="")
    deliverable_url = models.URLField(blank=True, null=True)
    deliverable_file = models.FileField(
        upload_to="milestone_deliveries/", blank=True, null=True
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order_num", "created_at"]

    def __str__(self):
        return f"Milestone #{self.order_num}: {self.title} (${self.amount})"
