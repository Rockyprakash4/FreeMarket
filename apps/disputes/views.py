from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Dispute
from .forms import DisputeForm, DisputeResolutionForm
from orders.models import Order
from payments.models import Payment
from notifications.models import Notification


@login_required
def open_dispute_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.user != order.client and request.user != order.freelancer:
        messages.error(request, "Only direct participants of this order can open a dispute.")
        return redirect("orders:order_detail", order_id=order.id)

    active_dispute = Dispute.objects.filter(
        order=order, status__in=[Dispute.Status.OPEN, Dispute.Status.UNDER_REVIEW]
    ).first()
    if active_dispute:
        messages.info(request, "A dispute is already open for this order.")
        return redirect("disputes:dispute_detail", dispute_id=active_dispute.id)

    if request.method == "POST":
        form = DisputeForm(request.POST, request.FILES)
        if form.is_valid():
            dispute = form.save(commit=False)
            dispute.order = order
            dispute.raised_by = request.user
            dispute.status = Dispute.Status.OPEN
            dispute.save()

            order.status = Order.Status.DISPUTED
            order.save()

            counterparty = order.freelancer if request.user == order.client else order.client
            Notification.objects.create(
                recipient=counterparty,
                title="Dispute Opened on Order",
                message=f"{request.user.get_display_name()} opened a dispute on Order #{order.id}: {dispute.get_reason_display()}.",
                link_url=f"/disputes/{dispute.id}/",
                notification_type=Notification.NotificationType.SYSTEM,
            )

            messages.success(
                request,
                f"Dispute #{dispute.id} has been opened. An administrator will review all evidence.",
            )
            return redirect("disputes:dispute_detail", dispute_id=dispute.id)
    else:
        form = DisputeForm()

    return render(request, "disputes/open_dispute.html", {"form": form, "order": order})


@login_required
def dispute_detail_view(request, dispute_id):
    dispute = get_object_or_404(
        Dispute.objects.select_related("order", "raised_by", "resolved_by"),
        id=dispute_id,
    )
    order = dispute.order

    if (
        request.user != order.client
        and request.user != order.freelancer
        and not request.user.is_staff
    ):
        messages.error(request, "Unauthorized access to dispute details.")
        return redirect("core:dashboard")

    resolution_form = None
    if request.user.is_staff:
        resolution_form = DisputeResolutionForm(instance=dispute)

    return render(
        request,
        "disputes/dispute_detail.html",
        {
            "dispute": dispute,
            "order": order,
            "resolution_form": resolution_form,
            "is_staff": request.user.is_staff,
        },
    )


@login_required
def admin_resolve_dispute_view(request, dispute_id):
    if not request.user.is_staff:
        messages.error(request, "Staff privileges required to resolve disputes.")
        return redirect("core:dashboard")

    dispute = get_object_or_404(Dispute, id=dispute_id)
    order = dispute.order

    if request.method == "POST":
        form = DisputeResolutionForm(request.POST, instance=dispute)
        if form.is_valid():
            disp = form.save(commit=False)
            disp.resolved_by = request.user
            disp.resolved_at = timezone.now()
            disp.save()

            payment = Payment.objects.filter(order=order).first()

            if disp.status == Dispute.Status.RESOLVED_REFUND:
                order.status = Order.Status.CANCELLED
                order.save()
                if payment:
                    payment.status = Payment.Status.REFUNDED
                    payment.save()
                msg = f"Dispute #{disp.id} resolved with full refund to client."

            elif disp.status == Dispute.Status.RESOLVED_PAYOUT:
                order.status = Order.Status.COMPLETED
                order.save()
                if payment:
                    payment.status = Payment.Status.RELEASED
                    payment.save()
                msg = f"Dispute #{disp.id} resolved with payout released to freelancer."

            else:
                order.status = Order.Status.ACTIVE
                order.save()
                msg = f"Dispute #{disp.id} dismissed; contract restored."

            Notification.objects.create(
                recipient=order.client,
                title="Dispute Resolved by Admin",
                message=f"Determination on Order #{order.id}: {disp.get_status_display()}.",
                link_url=f"/disputes/{disp.id}/",
                notification_type=Notification.NotificationType.SYSTEM,
            )
            Notification.objects.create(
                recipient=order.freelancer,
                title="Dispute Resolved by Admin",
                message=f"Determination on Order #{order.id}: {disp.get_status_display()}.",
                link_url=f"/disputes/{disp.id}/",
                notification_type=Notification.NotificationType.SYSTEM,
            )

            messages.success(request, msg)
            return redirect("disputes:dispute_detail", dispute_id=disp.id)

    return redirect("disputes:dispute_detail", dispute_id=dispute.id)


@login_required
def dispute_list_view(request):
    if request.user.is_staff:
        disputes = Dispute.objects.all().select_related("order", "raised_by")
    else:
        disputes = Dispute.objects.filter(
            order__client=request.user
        ) | Dispute.objects.filter(order__freelancer=request.user)
        disputes = disputes.distinct().select_related("order", "raised_by")

    return render(request, "disputes/dispute_list.html", {"disputes": disputes})
