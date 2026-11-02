from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review
from .forms import ReviewForm
from orders.models import Order
from notifications.models import Notification


@login_required
def create_review_view(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("client", "freelancer", "project"),
        id=order_id,
    )

    # Check that order is COMPLETED
    if order.status != Order.Status.COMPLETED:
        messages.warning(
            request, "Reviews can only be submitted for completed and approved orders."
        )
        return redirect("orders:order_detail", order_id=order.id)

    # Determine reviewer and reviewee
    if request.user == order.client:
        reviewee = order.freelancer
    elif request.user == order.freelancer:
        reviewee = order.client
    else:
        messages.error(request, "You are not a participant in this order.")
        return redirect("core:dashboard")

    # Check for existing review
    existing_review = Review.objects.filter(order=order, reviewer=request.user).first()
    if existing_review:
        messages.info(request, "You have already submitted a review for this order.")
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.order = order
            review.reviewer = request.user
            review.reviewee = reviewee
            review.save()

            Notification.objects.create(
                recipient=reviewee,
                title="New Review Received ⭐",
                message=f"{request.user.get_display_name()} gave you a {review.rating}-star review for '{order.project.title}'.",
                link_url=f"/orders/{order.id}/",
                notification_type=Notification.NotificationType.REVIEW_RECEIVED,
            )

            messages.success(
                request,
                f"Thank you! Your {review.rating}-star review for {reviewee.get_display_name()} has been published.",
            )
            return redirect("orders:order_detail", order_id=order.id)
        else:
            messages.error(request, "Please check the form for errors.")
    else:
        form = ReviewForm()

    context = {
        "form": form,
        "order": order,
        "reviewee": reviewee,
    }
    return render(request, "reviews/create_review.html", context)
