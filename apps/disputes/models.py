from django.db import models
from django.conf import settings


class Dispute(models.Model):
    class Reason(models.TextChoices):
        QUALITY = "quality", "Deliverables Do Not Meet Specification"
        DEADLINE = "deadline", "Significant Unexcused Delay"
        NON_RESPONSIVE = "non_responsive", "Counterparty Stopped Communicating"
        SCOPE = "scope", "Disagreement Over Scope of Work"
        OTHER = "other", "Other Discrepancy"

    class Status(models.TextChoices):
        OPEN = "open", "Dispute Opened"
        UNDER_REVIEW = "under_review", "Under Administrator Review"
        RESOLVED_REFUND = "resolved_refund", "Resolved - Refunded to Client"
        RESOLVED_PAYOUT = "resolved_payout", "Resolved - Payout to Freelancer"
        DISMISSED = "dismissed", "Dismissed (Agreement Maintained)"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="disputes",
    )
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="disputes_raised",
    )
    reason = models.CharField(
        max_length=50,
        choices=Reason.choices,
        default=Reason.QUALITY,
    )
    description = models.TextField(
        help_text="Detailed factual explanation of the issue and expected resolution"
    )
    evidence_file = models.FileField(
        upload_to="dispute_evidence/", blank=True, null=True
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN,
    )
    resolution_notes = models.TextField(blank=True, default="")
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="disputes_resolved",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Dispute #{self.id} on Order #{self.order.id} ({self.get_status_display()})"
