from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from django.conf import settings
from .models import Proposal
from .forms import ProposalForm
from marketplace.models import Project
from orders.models import Order
from payments.models import Payment
from messaging.models import Conversation, Message
from notifications.models import Notification


@login_required
def proposal_submit_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.user.role != request.user.Role.FREELANCER and not request.user.is_superuser:
        messages.error(request, "Only freelancer accounts can submit proposals to projects.")
        return redirect("marketplace:project_detail", project_id=project.id)

    if project.client == request.user:
        messages.error(request, "You cannot submit a proposal to your own project.")
        return redirect("marketplace:project_detail", project_id=project.id)

    if not project.is_open:
        messages.warning(request, "This project is no longer accepting proposals.")
        return redirect("marketplace:project_detail", project_id=project.id)

    existing = Proposal.objects.filter(project=project, freelancer=request.user).first()
    if existing:
        messages.info(request, "You have already submitted a proposal for this project.")
        return redirect("marketplace:project_detail", project_id=project.id)

    if request.method == "POST":
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.project = project
            proposal.freelancer = request.user
            proposal.status = Proposal.Status.PENDING
            proposal.save()

            # Create Notification for project client
            Notification.objects.create(
                recipient=project.client,
                title="New Proposal Received",
                message=f"'{request.user.get_display_name()}' submitted a proposal of ${proposal.proposed_price} on '{project.title}'.",
                link_url=f"/projects/{project.id}/proposals/",
                notification_type=Notification.NotificationType.PROPOSAL_RECEIVED,
            )

            messages.success(
                request,
                f"Your proposal for '${proposal.proposed_price}' has been successfully submitted to {project.client.get_display_name()}!",
            )
            return redirect("marketplace:project_detail", project_id=project.id)
        else:
            messages.error(request, "Please check the form for errors.")
    else:
        form = ProposalForm(
            initial={"proposed_price": project.budget, "estimated_delivery_days": 7}
        )

    return render(
        request,
        "proposals/proposal_form.html",
        {"form": form, "project": project},
    )


@login_required
def project_proposals_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, client=request.user)
    proposals = (
        Proposal.objects.filter(project=project)
        .select_related("freelancer", "freelancer__profile")
        .order_by("-created_at")
    )
    return render(
        request,
        "proposals/project_proposals.html",
        {"project": project, "proposals": proposals},
    )


@login_required
def proposal_accept_view(request, proposal_id):
    proposal = get_object_or_404(
        Proposal.objects.select_related("project", "freelancer", "project__client"),
        id=proposal_id,
    )
    project = proposal.project

    if project.client != request.user and not request.user.is_superuser:
        messages.error(request, "Unauthorized access. You do not own this project.")
        return redirect("marketplace:project_list")

    if request.method == "POST":
        if proposal.status != Proposal.Status.PENDING:
            messages.warning(request, f"This proposal has already been {proposal.status}.")
            return redirect("proposals:project_proposals", project_id=project.id)

        commission_pct = Decimal(str(getattr(settings, "PLATFORM_COMMISSION_PERCENT", 10.0)))
        total_amount = proposal.proposed_price
        platform_fee = (total_amount * (commission_pct / Decimal("100.0"))).quantize(
            Decimal("0.01")
        )
        freelancer_payout = total_amount - platform_fee

        # 1. Update proposal status
        proposal.status = Proposal.Status.ACCEPTED
        proposal.save()

        # 2. Update project status
        project.status = Project.Status.IN_PROGRESS
        project.save()

        # 3. Create active Order
        order = Order.objects.create(
            project=project,
            proposal=proposal,
            client=project.client,
            freelancer=proposal.freelancer,
            total_amount=total_amount,
            platform_fee=platform_fee,
            freelancer_payout=freelancer_payout,
            status=Order.Status.ACTIVE,
        )

        # 4. Create safe mock Escrow Payment
        payment = Payment.objects.create(
            order=order,
            payer=project.client,
            amount=total_amount,
            platform_fee=platform_fee,
            net_payout=freelancer_payout,
            status=Payment.Status.HELD_IN_ESCROW,
        )

        # 5. Decline other proposals on this project
        other_proposals = Proposal.objects.filter(
            project=project, status=Proposal.Status.PENDING
        ).exclude(id=proposal.id)
        for other in other_proposals:
            other.status = Proposal.Status.REJECTED
            other.save()
            Notification.objects.create(
                recipient=other.freelancer,
                title="Project Proposal Update",
                message=f"The client has selected another developer for '{project.title}'. Thank you for your application.",
                link_url=f"/projects/{project.id}/",
                notification_type=Notification.NotificationType.PROPOSAL_REJECTED,
            )

        # 6. Create conversation for the order
        conversation = Conversation.objects.filter(
            project=project, participants=project.client
        ).filter(participants=proposal.freelancer).first()
        if not conversation:
            conversation = Conversation.objects.create(project=project)
            conversation.participants.add(project.client, proposal.freelancer)

        Message.objects.create(
            conversation=conversation,
            sender=project.client,
            content=f"Hello {proposal.freelancer.get_display_name()}! I have accepted your proposal for '{project.title}'. Looking forward to collaborating!",
        )

        # 7. Notify Freelancer
        Notification.objects.create(
            recipient=proposal.freelancer,
            title="Congratulations! Proposal Accepted 🎉",
            message=f"{project.client.get_display_name()} accepted your proposal for '{project.title}'. An active order #{order.id} has been created and funds are secured in escrow.",
            link_url=f"/orders/{order.id}/",
            notification_type=Notification.NotificationType.PROPOSAL_ACCEPTED,
        )

        messages.success(
            request,
            f"You have accepted {proposal.freelancer.get_display_name()}'s proposal! Order #{order.id} is now active.",
        )
        return redirect("orders:order_detail", order_id=order.id)

    return render(
        request,
        "proposals/confirm_accept.html",
        {"proposal": proposal, "project": project},
    )


@login_required
def proposal_reject_view(request, proposal_id):
    proposal = get_object_or_404(
        Proposal.objects.select_related("project", "freelancer", "project__client"),
        id=proposal_id,
    )
    if proposal.project.client != request.user and not request.user.is_superuser:
        messages.error(request, "Unauthorized access.")
        return redirect("marketplace:project_list")

    if request.method == "POST":
        proposal.status = Proposal.Status.REJECTED
        proposal.save()

        Notification.objects.create(
            recipient=proposal.freelancer,
            title="Proposal Update",
            message=f"Your proposal for '{proposal.project.title}' was declined by the client.",
            link_url=f"/projects/{proposal.project.id}/",
            notification_type=Notification.NotificationType.PROPOSAL_REJECTED,
        )
        messages.info(request, "The proposal has been marked as declined.")
        return redirect("proposals:project_proposals", project_id=proposal.project.id)

    return render(
        request,
        "proposals/confirm_reject.html",
        {"proposal": proposal},
    )


@login_required
def proposal_withdraw_view(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id, freelancer=request.user)

    if proposal.status != Proposal.Status.PENDING:
        messages.warning(request, f"You cannot withdraw a proposal that is {proposal.status}.")
        return redirect("marketplace:project_detail", project_id=proposal.project.id)

    if request.method == "POST":
        proposal.status = Proposal.Status.WITHDRAWN
        proposal.save()
        messages.info(request, "Your proposal has been withdrawn.")
        return redirect("marketplace:project_detail", project_id=proposal.project.id)

    return render(
        request,
        "proposals/confirm_withdraw.html",
        {"proposal": proposal},
    )
