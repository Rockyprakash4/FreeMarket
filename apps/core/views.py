from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from marketplace.models import Project, Category, Service
from proposals.models import Proposal
from orders.models import Order
from accounts.models import User, Profile
from notifications.models import Notification
from payments.models import Payment
from disputes.models import Dispute
from reviews.models import Review


def home_view(request):
    categories = Category.objects.filter(is_featured=True)[:6]
    featured_projects = (
        Project.objects.filter(status=Project.Status.OPEN)
        .select_related("client", "category")
        .order_by("-created_at")[:6]
    )
    featured_services = (
        Service.objects.filter(is_active=True)
        .select_related("freelancer", "freelancer__profile", "category")
        .order_by("-views_count", "-created_at")[:4]
    )
    top_freelancers = (
        User.objects.filter(role=User.Role.FREELANCER, is_active=True)
        .select_related("profile")
        .order_by("-profile__rating", "-created_at")[:4]
    )

    stats = {
        "projects_count": Project.objects.count(),
        "freelancers_count": User.objects.filter(role=User.Role.FREELANCER).count(),
        "services_count": Service.objects.filter(is_active=True).count(),
        "completed_orders": Order.objects.filter(status=Order.Status.COMPLETED).count(),
    }

    context = {
        "categories": categories,
        "featured_projects": featured_projects,
        "featured_services": featured_services,
        "top_freelancers": top_freelancers,
        "stats": stats,
    }
    return render(request, "core/home.html", context)


@login_required
def dashboard_view(request):
    user = request.user
    context = {"user": user}

    if user.role == User.Role.CLIENT or user.is_superuser:
        my_projects = (
            Project.objects.filter(client=user)
            .select_related("category")
            .order_by("-created_at")
        )
        my_orders = (
            Order.objects.filter(client=user)
            .select_related("project", "service", "freelancer")
            .order_by("-created_at")
        )
        pending_proposals = (
            Proposal.objects.filter(
                project__client=user, status=Proposal.Status.PENDING
            )
            .select_related("project", "freelancer", "freelancer__profile")
            .order_by("-created_at")[:5]
        )

        total_projects = my_projects.count()
        active_projects = my_projects.filter(
            status__in=[Project.Status.OPEN, Project.Status.IN_PROGRESS]
        ).count()
        active_orders = my_orders.filter(
            status__in=[Order.Status.ACTIVE, Order.Status.DELIVERED, Order.Status.IN_REVISION]
        ).count()

        shortlisted_freelancers = getattr(user.profile, "saved_freelancers", None)
        shortlisted = shortlisted_freelancers.all()[:4] if shortlisted_freelancers else []

        context.update(
            {
                "is_client": True,
                "total_projects": total_projects,
                "active_projects": active_projects,
                "active_orders": active_orders,
                "my_projects": my_projects[:5],
                "my_orders": my_orders[:5],
                "pending_proposals": pending_proposals,
                "shortlisted": shortlisted,
                "total_spent": getattr(user.profile, "total_spent", 0.0),
            }
        )
    else:
        # Freelancer Dashboard
        my_proposals = (
            Proposal.objects.filter(freelancer=user)
            .select_related("project", "project__client")
            .order_by("-created_at")
        )
        my_orders = (
            Order.objects.filter(freelancer=user)
            .select_related("project", "service", "client")
            .order_by("-created_at")
        )
        my_services = Service.objects.filter(freelancer=user).order_by("-created_at")

        active_orders = my_orders.filter(
            status__in=[Order.Status.ACTIVE, Order.Status.DELIVERED, Order.Status.IN_REVISION]
        )
        pending_proposals = my_proposals.filter(status=Proposal.Status.PENDING)
        accepted_proposals = my_proposals.filter(status=Proposal.Status.ACCEPTED)

        recommended_projects = (
            Project.objects.filter(status=Project.Status.OPEN)
            .select_related("client", "category")
            .order_by("-created_at")[:4]
        )

        context.update(
            {
                "is_client": False,
                "total_proposals": my_proposals.count(),
                "pending_proposals_count": pending_proposals.count(),
                "accepted_proposals_count": accepted_proposals.count(),
                "active_orders_count": active_orders.count(),
                "my_proposals": my_proposals[:6],
                "my_orders": active_orders,
                "my_services": my_services,
                "recommended_projects": recommended_projects,
                "total_earned": getattr(user.profile, "total_earned", 0.0),
                "ai_score": getattr(user.profile, "ai_profile_score", 50),
            }
        )

    recent_notifications = Notification.objects.filter(recipient=user).order_by(
        "-created_at"
    )[:5]
    context["recent_notifications"] = recent_notifications

    return render(request, "core/dashboard.html", context)


@login_required
def admin_dashboard_view(request):
    """
    Dedicated Executive Admin Dashboard:
    Real-time platform statistics, moderation pipelines, dispute resolution,
    and commission tracking from MongoDB.
    """
    if not request.user.is_staff:
        messages.error(request, "Access restricted to SkillSphere Administrators.")
        return redirect("core:dashboard")

    total_users = User.objects.count()
    total_clients = User.objects.filter(role=User.Role.CLIENT).count()
    total_freelancers = User.objects.filter(role=User.Role.FREELANCER).count()
    total_projects = Project.objects.count()
    active_services = Service.objects.filter(is_active=True).count()

    all_orders = Order.objects.all()
    active_orders = all_orders.filter(status__in=[Order.Status.ACTIVE, Order.Status.DELIVERED, Order.Status.IN_REVISION]).count()
    completed_orders = all_orders.filter(status=Order.Status.COMPLETED).count()
    disputed_orders = all_orders.filter(status=Order.Status.DISPUTED).count()

    # Financial sums
    payments = Payment.objects.all()
    total_transacted = sum(p.amount for p in payments) if payments.exists() else 0.0
    total_commission = sum(p.platform_fee for p in payments) if payments.exists() else 0.0

    pending_disputes = Dispute.objects.filter(status__in=[Dispute.Status.OPEN, Dispute.Status.UNDER_REVIEW]).select_related("order", "raised_by")
    pending_verifications = Profile.objects.filter(verification_status=Profile.VerificationStatus.PENDING).select_related("user")
    reported_reviews = Review.objects.filter(is_reported=True).select_related("reviewer", "reviewee", "order")

    context = {
        "total_users": total_users,
        "total_clients": total_clients,
        "total_freelancers": total_freelancers,
        "total_projects": total_projects,
        "active_services": active_services,
        "active_orders": active_orders,
        "completed_orders": completed_orders,
        "disputed_orders": disputed_orders,
        "total_transacted": total_transacted,
        "total_commission": total_commission,
        "pending_disputes": pending_disputes,
        "pending_verifications": pending_verifications,
        "reported_reviews": reported_reviews,
        "recent_payments": payments.order_by("-created_at")[:6],
    }
    return render(request, "core/admin_dashboard.html", context)


def about_view(request):
    return render(request, "core/about.html")


def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name", "")
        email = request.POST.get("email", "")
        subject = request.POST.get("subject", "")
        message = request.POST.get("message", "")
        messages.success(
            request, f"Thank you, {name}! Your inquiry has been received. Our support team will follow up at {email}."
        )
        return redirect("core:contact")
    return render(request, "core/contact.html")


def terms_view(request):
    return render(request, "core/terms.html")
