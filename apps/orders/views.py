from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.conf import settings
from .models import Order, Milestone
from .forms import (
    DeliverySubmissionForm,
    RevisionRequestForm,
    MilestoneForm,
    MilestoneSubmissionForm,
)
from marketplace.models import Project, Service
from payments.models import Payment
from notifications.models import Notification
from reviews.models import Review
from messaging.models import Conversation, Message


@login_required
def order_list_view(request):
    if request.user.role == request.user.Role.CLIENT:
        orders = Order.objects.filter(client=request.user).select_related(
            "project", "service", "freelancer", "freelancer__profile"
        )
    else:
        orders = Order.objects.filter(freelancer=request.user).select_related(
            "project", "service", "client", "client__profile"
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
        Order.objects.select_related("project", "service", "client", "freelancer"),
        id=order_id,
    )

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
        and order.status in [Order.Status.ACTIVE, Order.Status.DELIVERED, Order.Status.IN_REVISION]
    ):
        delivery_form = DeliverySubmissionForm(instance=order)

    milestone_form = None
    if request.user == order.client or request.user == order.freelancer:
        milestone_form = MilestoneForm()

    payment = Payment.objects.filter(order=order).first()
    user_review = Review.objects.filter(order=order, reviewer=request.user).first()
    other_review = Review.objects.filter(
        order=order,
        reviewer=order.freelancer if request.user == order.client else order.client,
    ).first()
    milestones = order.milestones.all().order_by("order_num")
    revision_form = RevisionRequestForm()

    context = {
        "order": order,
        "payment": payment,
        "delivery_form": delivery_form,
        "milestones": milestones,
        "milestone_form": milestone_form,
        "revision_form": revision_form,
        "user_review": user_review,
        "other_review": other_review,
        "is_client": request.user == order.client,
        "is_freelancer": request.user == order.freelancer,
    }
    return render(request, "orders/order_detail.html", context)


@login_required
def order_deliver_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, freelancer=request.user)

    if order.status not in [Order.Status.ACTIVE, Order.Status.DELIVERED, Order.Status.IN_REVISION]:
        messages.warning(request, f"This order cannot be delivered in status: {order.status}.")
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        form = DeliverySubmissionForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = Order.Status.DELIVERED
            order.revision_requested = False
            order.delivered_at = timezone.now()
            order.save()

            Notification.objects.create(
                recipient=order.client,
                title="Work Delivered for Review",
                message=f"{request.user.get_display_name()} has submitted deliverables for '{order.title}'. Please review and approve.",
                link_url=f"/orders/{order.id}/",
                notification_type=Notification.NotificationType.ORDER_DELIVERED,
            )

            messages.success(
                request, "Deliverables submitted successfully! The client has been notified to review your work."
            )
            return redirect("orders:order_detail", order_id=order.id)
        else:
            messages.error(request, "Please check the form for errors.")

    return redirect("orders:order_detail", order_id=order.id)


@login_required
def order_request_revision_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, client=request.user)

    if order.status != Order.Status.DELIVERED:
        messages.warning(request, "You can only request revisions on delivered orders.")
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        form = RevisionRequestForm(request.POST)
        if form.is_valid():
            notes = form.cleaned_data["notes"]
            order.status = Order.Status.IN_REVISION
            order.revision_requested = True
            order.revision_notes = notes
            order.revision_count += 1
            order.save()

            Notification.objects.create(
                recipient=order.freelancer,
                title="Revision Requested",
                message=f"{request.user.get_display_name()} requested a revision on '{order.title}': {notes[:80]}...",
                link_url=f"/orders/{order.id}/",
                notification_type=Notification.NotificationType.SYSTEM,
            )

            messages.info(request, "Revision request dispatched to the freelancer.")
            return redirect("orders:order_detail", order_id=order.id)

    return redirect("orders:order_detail", order_id=order.id)


@login_required
def order_approve_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, client=request.user)

    if order.status not in [Order.Status.DELIVERED, Order.Status.IN_REVISION]:
        messages.warning(request, "You can only approve an order after deliverables have been submitted.")
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        order.status = Order.Status.COMPLETED
        order.completed_at = timezone.now()
        order.revision_requested = False
        order.save()

        if order.project:
            order.project.status = Project.Status.COMPLETED
            order.project.save()

        payment = Payment.objects.filter(order=order).first()
        if payment:
            payment.status = Payment.Status.RELEASED
            payment.save()

        f_profile = getattr(order.freelancer, "profile", None)
        if f_profile:
            f_profile.total_earned = Decimal(str(f_profile.total_earned or 0)) + Decimal(str(order.freelancer_payout))
            f_profile.save(update_fields=["total_earned"])

        c_profile = getattr(order.client, "profile", None)
        if c_profile:
            c_profile.total_spent = Decimal(str(c_profile.total_spent or 0)) + Decimal(str(order.total_amount))
            c_profile.save(update_fields=["total_spent"])

        Notification.objects.create(
            recipient=order.freelancer,
            title="Work Approved & Payment Released 🎉",
            message=f"{request.user.get_display_name()} approved the work for '{order.title}'. ${order.freelancer_payout} has been released to your balance!",
            link_url=f"/orders/{order.id}/",
            notification_type=Notification.NotificationType.ORDER_COMPLETED,
        )

        messages.success(
            request,
            f"You have approved the deliverables! Order #{order.id} is complete and escrow payout of ${order.freelancer_payout} is released.",
        )
        return redirect("reviews:create_review", order_id=order.id)

    return render(request, "orders/confirm_approve.html", {"order": order})


@login_required
def order_create_from_service_view(request, service_id):
    """Direct purchase of a Freelancer Service package."""
    service = get_object_or_404(Service, id=service_id, is_active=True)

    if request.user == service.freelancer:
        messages.error(request, "You cannot purchase your own service.")
        return redirect("marketplace:service_detail", service_id=service.id)

    commission_pct = Decimal(str(getattr(settings, "PLATFORM_COMMISSION_PERCENT", 10.0)))
    total_amount = service.price
    platform_fee = (total_amount * (commission_pct / Decimal("100.0"))).quantize(Decimal("0.01"))
    freelancer_payout = total_amount - platform_fee

    if request.method == "POST":
        order = Order.objects.create(
            service=service,
            client=request.user,
            freelancer=service.freelancer,
            total_amount=total_amount,
            platform_fee=platform_fee,
            freelancer_payout=freelancer_payout,
            status=Order.Status.ACTIVE,
        )

        payment = Payment.objects.create(
            order=order,
            payer=request.user,
            amount=total_amount,
            platform_fee=platform_fee,
            net_payout=freelancer_payout,
            status=Payment.Status.HELD_IN_ESCROW,
        )

        # Create conversation
        conv = Conversation.objects.filter(participants=request.user).filter(participants=service.freelancer).first()
        if not conv:
            conv = Conversation.objects.create()
            conv.participants.add(request.user, service.freelancer)

        Message.objects.create(
            conversation=conv,
            sender=request.user,
            content=f"Hello! I just ordered your service '{service.title}' (Order #{order.id}). Looking forward to working together!",
        )

        Notification.objects.create(
            recipient=service.freelancer,
            title="New Service Order Received 🎉",
            message=f"{request.user.get_display_name()} ordered your service '{service.title}'. Escrow of ${total_amount} is secured.",
            link_url=f"/orders/{order.id}/",
            notification_type=Notification.NotificationType.SYSTEM,
        )

        messages.success(request, f"Order #{order.id} placed successfully! Escrow funds secured.")
        return redirect("orders:order_detail", order_id=order.id)

    return render(
        request,
        "orders/confirm_service_order.html",
        {
            "service": service,
            "total_amount": total_amount,
            "platform_fee": platform_fee,
            "freelancer_payout": freelancer_payout,
        },
    )


# --- MILESTONE WORKFLOWS ---

@login_required
def milestone_create_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.user != order.client and request.user != order.freelancer:
        messages.error(request, "Unauthorized access.")
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        form = MilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.order = order
            milestone.order_num = order.milestones.count() + 1
            milestone.status = Milestone.Status.IN_PROGRESS
            milestone.save()
            messages.success(request, f"Milestone '{milestone.title}' added to Order #{order.id}!")
        else:
            messages.error(request, "Please check milestone form errors.")

    return redirect("orders:order_detail", order_id=order.id)


@login_required
def milestone_submit_view(request, milestone_id):
    milestone = get_object_or_404(Milestone, id=milestone_id)
    order = milestone.order

    if request.user != order.freelancer:
        messages.error(request, "Only the assigned developer can submit milestone deliverables.")
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        form = MilestoneSubmissionForm(request.POST, request.FILES, instance=milestone)
        if form.is_valid():
            m = form.save(commit=False)
            m.status = Milestone.Status.SUBMITTED
            m.submitted_at = timezone.now()
            m.save()

            Notification.objects.create(
                recipient=order.client,
                title="Milestone Work Submitted",
                message=f"{request.user.get_display_name()} submitted work for Milestone '{m.title}'.",
                link_url=f"/orders/{order.id}/",
                notification_type=Notification.NotificationType.ORDER_DELIVERED,
            )
            messages.success(request, f"Milestone '{m.title}' submitted for review!")
        else:
            messages.error(request, "Submission form error.")

    return redirect("orders:order_detail", order_id=order.id)


@login_required
def milestone_approve_view(request, milestone_id):
    milestone = get_object_or_404(Milestone, id=milestone_id)
    order = milestone.order

    if request.user != order.client and not request.user.is_superuser:
        messages.error(request, "Only the client can approve milestone deliverables.")
        return redirect("orders:order_detail", order_id=order.id)

    if request.method == "POST":
        milestone.status = Milestone.Status.APPROVED
        milestone.approved_at = timezone.now()
        milestone.save()

        Notification.objects.create(
            recipient=order.freelancer,
            title="Milestone Approved! ✓",
            message=f"{request.user.get_display_name()} approved Milestone '{milestone.title}' (${milestone.amount}).",
            link_url=f"/orders/{order.id}/",
            notification_type=Notification.NotificationType.ORDER_COMPLETED,
        )
        messages.success(request, f"Milestone '{milestone.title}' approved successfully!")

    return redirect("orders:order_detail", order_id=order.id)
