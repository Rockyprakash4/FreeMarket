from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from marketplace.models import Project, Category
from proposals.models import Proposal
from orders.models import Order
from accounts.models import User
from notifications.models import Notification


def home_view(request):
    categories = Category.objects.filter(is_featured=True)[:6]
    featured_projects = (
        Project.objects.filter(status=Project.Status.OPEN)
        .select_related("client", "category")
        .order_by("-created_at")[:6]
    )
    top_freelancers = (
        User.objects.filter(role=User.Role.FREELANCER, is_active=True)
        .select_related("profile")
        .order_by("-profile__rating", "-created_at")[:4]
    )

    stats = {
        "projects_count": Project.objects.count(),
        "freelancers_count": User.objects.filter(role=User.Role.FREELANCER).count(),
        "completed_orders": Order.objects.filter(status=Order.Status.COMPLETED).count(),
    }

    context = {
        "categories": categories,
        "featured_projects": featured_projects,
        "top_freelancers": top_freelancers,
        "stats": stats,
    }
    return render(request, "core/home.html", context)


@login_required
def dashboard_view(request):
    user = request.user
    context = {"user": user}

    if user.role == User.Role.CLIENT or user.is_superuser:
        # Client statistics & projects
        my_projects = (
            Project.objects.filter(client=user)
            .select_related("category")
            .order_by("-created_at")
        )
        my_orders = (
            Order.objects.filter(client=user)
            .select_related("project", "freelancer")
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
            status__in=[Order.Status.ACTIVE, Order.Status.DELIVERED]
        ).count()

        context.update(
            {
                "is_client": True,
                "total_projects": total_projects,
                "active_projects": active_projects,
                "active_orders": active_orders,
                "my_projects": my_projects[:5],
                "my_orders": my_orders[:5],
                "pending_proposals": pending_proposals,
                "total_spent": getattr(user.profile, "total_spent", 0.0),
            }
        )
    else:
        # Freelancer statistics & proposals
        my_proposals = (
            Proposal.objects.filter(freelancer=user)
            .select_related("project", "project__client")
            .order_by("-created_at")
        )
        my_orders = (
            Order.objects.filter(freelancer=user)
            .select_related("project", "client")
            .order_by("-created_at")
        )

        active_orders = my_orders.filter(
            status__in=[Order.Status.ACTIVE, Order.Status.DELIVERED]
        )
        pending_proposals = my_proposals.filter(status=Proposal.Status.PENDING)
        accepted_proposals = my_proposals.filter(status=Proposal.Status.ACCEPTED)

        # Recommended open projects
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
                "active_orders": active_orders,
                "recommended_projects": recommended_projects,
                "total_earned": getattr(user.profile, "total_earned", 0.0),
            }
        )

    # Recent notifications
    recent_notifications = Notification.objects.filter(recipient=user).order_by(
        "-created_at"
    )[:5]
    context["recent_notifications"] = recent_notifications

    return render(request, "core/dashboard.html", context)


def terms_view(request):
    return render(request, "core/terms.html")


def about_view(request):
    return render(request, "core/about.html")
