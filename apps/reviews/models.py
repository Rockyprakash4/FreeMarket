from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    service = models.ForeignKey(
        "marketplace.Service",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_given",
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_received",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
        help_text="Rating between 1 and 5 stars",
    )
    comment = models.TextField()
    is_reported = models.BooleanField(
        default=False, help_text="Flagged for inappropriate content"
    )
    is_moderated = models.BooleanField(
        default=False, help_text="Reviewed by platform administrator"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "reviewer"],
                name="unique_review_per_order_per_reviewer",
            )
        ]

    def __str__(self):
        return f"Review ({self.rating}★) by {self.reviewer.username} for {self.reviewee.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update reviewee's aggregate profile rating
        profile = getattr(self.reviewee, "profile", None)
        if profile:
            reviews = Review.objects.filter(reviewee=self.reviewee, is_reported=False)
            total = reviews.count()
            if total > 0:
                avg = sum(r.rating for r in reviews) / total
                profile.rating = round(avg, 2)
                profile.reviews_count = total
                profile.save(update_fields=["rating", "reviews_count"])
