from django.db import models
from django.conf import settings


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        PROPOSAL_RECEIVED = "proposal_received", "New Proposal Received"
        PROPOSAL_ACCEPTED = "proposal_accepted", "Proposal Accepted"
        PROPOSAL_REJECTED = "proposal_rejected", "Proposal Declined"
        ORDER_DELIVERED = "order_delivered", "Work Delivered for Review"
        ORDER_COMPLETED = "order_completed", "Order Approved & Completed"
        NEW_MESSAGE = "new_message", "New Direct Message"
        REVIEW_RECEIVED = "review_received", "New Client/Freelancer Review"
        SYSTEM = "system", "System Notification"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    link_url = models.CharField(max_length=255, blank=True, default="")
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"
