from django.db import models
from django.conf import settings


class Proposal(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Declined"
        WITHDRAWN = "withdrawn", "Withdrawn"

    project = models.ForeignKey(
        "marketplace.Project",
        on_delete=models.CASCADE,
        related_name="proposals",
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="proposals_submitted",
    )
    cover_letter = models.TextField(help_text="Why you are a great fit for this project")
    proposed_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Total proposed price in USD"
    )
    estimated_delivery_days = models.PositiveIntegerField(
        default=7, help_text="Estimated delivery time in days"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "freelancer"],
                name="unique_proposal_per_freelancer_per_project",
            )
        ]

    def __str__(self):
        return f"Proposal by {self.freelancer.username} on '{self.project.title}'"
