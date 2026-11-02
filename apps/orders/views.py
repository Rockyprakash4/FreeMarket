from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Order
from .forms import DeliverySubmissionForm
from marketplace.models import Project
from payments.models import Payment
from notifications.models import Notification
from reviews.models import Review


@login_required
def order_list_view(request):
    if request.user.role == request.user.Role.CLIENT:
        orders = Order.objects.filter(client=request.user).select_related(
            "project", "freelancer", "freelancer__profile"
        )
    else:
        orders = Order.objects.filter(freelancer=request.user).select_related(
            "project", "client", "client__profile"
        )

    status_filter = request.GET.get("status")
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(
        request,
        "orders/order_list.html",
        {"orders": orders, "selected_status": status_filter},
    )


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("project", "client", "freelancer"),
        id=order_id,
    )

    # Authorization check
    if (
        request.user != order.client
        and request.user != order.freelancer
        and not request.user.is_superuser
    ):
        messages.error(request, "You do not have permission to view this order.")
        return redirect("core:dashboard")

    delivery_form = None
    if (
        request.user == order.freelancer
        and order.status in [Order.Status.ACTIVE, Order.Status.DELIVERED]
    ):
        delivery_form = DeliverySubmissionForm(instance=order)

    payment = Payment.objects.filter(order=order).first()
    user_review = Review.objects.filter(order=order, reviewer=request.user).first()
    other_review = Review.objects.filter(
        order=order,
        reviewer=order.freelancer if request.user == order.client else order.client,
    ).first()

    context = {
        "order": order,
        "payment": payment,
        "delivery_form": delivery_form,
        "user_review": user_review,
        "other_review": other_review,
        "is_client": request.user == order.client,
        "is_freelancer": request.user == order.freelancer,
    }
    return render(request, "orders/order_detail.html", context)


@login_required
def order_deliver_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, freelancer=request.user)

    if order.status not in [Order.Status.ACTIVE, Order.Status.DELIVERED]:
        messages.warning(request, f"This order cannot be delivered in state: {order.status}.")
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        form = DeliverySubmissionForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = Order.Status.DELIVERED
            order.delivered_at = timezone.now()
            order.save()

            # Notify Client
            Notification.objects.create(
                recipient=order.client,
                title="Work Delivered for Review",
                message=f"{request.user.get_display_name()} has submitted deliverables for '{order.project.title}'. Please review and approve.",
                link_url=f"/orders/{order.id}/",
                notification_type=Notification.NotificationType.ORDER_DELIVERED,
            )

            messages.success(
                request,
                "Deliverables submitted successfully! The client has been notified to review your work.",
            )
            return redirect("orders:order_detail", order_id=order.id)
        else:
            messages.error(request, "Please check the form for errors.")

    return redirect("orders:order_detail", order_id=order.id)


@login_required
def order_approve_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, client=request.user)

    if order.status != Order.Status.DELIVERED:
        messages.warning(
            request, "You can only approve an order after deliverables have been submitted."
        )
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        order.status = Order.Status.COMPLETED
        order.completed_at = timezone.now()
        order.save()

        # Update Project
        order.project.status = Project.Status.COMPLETED
        order.project.save()

        # Release Escrow Payment
        payment = Payment.objects.filter(order=order).first()
        if payment:
            payment.status = Payment.Status.RELEASED
            payment.save()

        # Update Freelancer Earnings
        f_profile = getattr(order.freelancer, "profile", None)
        if f_profile:
            f_profile.total_earned += order.freelancer_payout
            f_profile.save(update_fields=["total_earned"])

        # Update Client Spending
        c_profile = getattr(order.client, "profile", None)
        if c_profile:
            c_profile.total_spent += order.total_amount
            c_profile.save(update_fields=["total_spent"])

        # Notify Freelancer
        Notification.objects.create(
            recipient=order.freelancer,
            title="Work Approved & Payment Released 🎉",
            message=f"{request.user.get_display_name()} approved the work for '{order.project.title}'. ${order.freelancer_payout} has been released to your balance!",
            link_url=f"/orders/{order.id}/",
            notification_type=Notification.NotificationType.ORDER_COMPLETED,
        )

        messages.success(
            request,
            f"You have approved the deliverables! Order #{order.id} is complete and escrow payout of ${order.freelancer_payout} is released.",
        )
        return redirect("reviews:create_review", order_id=order.id)

    return render(
        request,
        "orders/confirm_approve.html",
        {"order": order},
    )
