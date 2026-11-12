from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Profile
from .forms import (
    SkillSphereRegistrationForm,
    SkillSphereLoginForm,
    UserProfileForm,
    FreelancerProfileForm,
    PasswordResetRequestForm,
    PasswordResetConfirmForm,
)
from reviews.models import Review
from orders.models import Order
from core.ai_engine import analyze_freelancer_profile


def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = SkillSphereRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome to SkillSphere, {user.first_name or user.username}! Your account has been initialized.",
            )
            return redirect("core:dashboard")
        else:
            messages.error(
                request, "Please correct the errors below to create your account."
            )
    else:
        initial_role = request.GET.get("role", User.Role.FREELANCER)
        if initial_role not in [User.Role.CLIENT, User.Role.FREELANCER]:
            initial_role = User.Role.FREELANCER
        form = SkillSphereRegistrationForm(initial={"role": initial_role})

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = SkillSphereLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_display_name()}!")
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("core:dashboard")
        else:
            messages.error(request, "Invalid credentials. Please verify your username and password.")
    else:
        form = SkillSphereLoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out from SkillSphere.")
    return redirect("core:home")


@login_required
def profile_edit_view(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)
        profile_form = FreelancerProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            saved_profile = profile_form.save()

            # Trigger AI profile & resume analysis
            resume_path = saved_profile.resume.path if saved_profile.resume else None
            ai_analysis = analyze_freelancer_profile(saved_profile, resume_path)

            messages.success(
                request,
                f"Your profile has been updated! AI Completeness Score: {ai_analysis['score']}%",
            )
            return redirect("accounts:profile_edit")
        else:
            messages.error(request, "Please check the form for errors and try again.")
    else:
        user_form = UserProfileForm(instance=user)
        profile_form = FreelancerProfileForm(instance=profile)

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "profile": profile,
    }
    return render(request, "accounts/profile_edit.html", context)


@login_required
def submit_verification_view(request):
    """Freelancer submits identity/portfolio verification documents."""
    profile = request.user.profile
    if request.method == "POST" and "verification_document" in request.FILES:
        profile.verification_document = request.FILES["verification_document"]
        profile.verification_status = Profile.VerificationStatus.PENDING
        profile.save(update_fields=["verification_document", "verification_status"])
        messages.success(
            request, "Verification documents submitted successfully! Admin review in progress."
        )
    return redirect("accounts:profile_edit")


@login_required
def verify_email_view(request):
    """Simulate instant email verification link."""
    user = request.user
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    messages.success(request, "Email address verified successfully!")
    return redirect("core:dashboard")


@login_required
def shortlist_toggle_view(request, username):
    """Client shortlists or un-shortlists a freelancer."""
    target_freelancer = get_object_or_404(User, username=username, role=User.Role.FREELANCER)
    client_profile, _ = Profile.objects.get_or_create(user=request.user)

    if target_freelancer in client_profile.saved_freelancers.all():
        client_profile.saved_freelancers.remove(target_freelancer)
        messages.info(request, f"Removed {target_freelancer.get_display_name()} from your shortlist.")
    else:
        client_profile.saved_freelancers.add(target_freelancer)
        messages.success(request, f"Added {target_freelancer.get_display_name()} to your shortlist!")

    return redirect(request.META.get("HTTP_REFERER", "accounts:freelancer_list"))


def freelancer_list_view(request):
    freelancers = (
        User.objects.filter(role=User.Role.FREELANCER, is_active=True)
        .select_related("profile")
        .order_by("-profile__rating", "-created_at")
    )

    query = request.GET.get("q", "").strip()
    skill_filter = request.GET.get("skill", "").strip()
    exp_filter = request.GET.get("experience", "").strip()
    avail_filter = request.GET.get("availability", "").strip()
    verified_only = request.GET.get("verified") == "1"

    if query:
        freelancers = freelancers.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(profile__headline__icontains=query)
            | Q(profile__skills__icontains=query)
            | Q(profile__bio__icontains=query)
        )
    if skill_filter:
        freelancers = freelancers.filter(profile__skills__icontains=skill_filter)
    if exp_filter:
        freelancers = freelancers.filter(profile__experience_level=exp_filter)
    if avail_filter:
        freelancers = freelancers.filter(profile__availability=avail_filter)
    if verified_only:
        freelancers = freelancers.filter(profile__verification_status=Profile.VerificationStatus.VERIFIED)

    paginator = Paginator(freelancers, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Shortlisted IDs for current client
    shortlisted_ids = set()
    if request.user.is_authenticated and hasattr(request.user, "profile"):
        shortlisted_ids = set(request.user.profile.saved_freelancers.values_list("id", flat=True))

    context = {
        "page_obj": page_obj,
        "query": query,
        "skill_filter": skill_filter,
        "exp_filter": exp_filter,
        "avail_filter": avail_filter,
        "verified_only": verified_only,
        "shortlisted_ids": shortlisted_ids,
        "total_count": paginator.count,
    }
    return render(request, "accounts/freelancer_list.html", context)


def freelancer_profile_view(request, username):
    freelancer = get_object_or_404(User, username=username, role=User.Role.FREELANCER)
    profile, _ = Profile.objects.get_or_create(user=freelancer)
    services = freelancer.services_offered.filter(is_active=True)
    completed_orders = Order.objects.filter(
        freelancer=freelancer, status=Order.Status.COMPLETED
    ).order_by("-completed_at")[:6]
    reviews = Review.objects.filter(reviewee=freelancer, is_reported=False).order_by("-created_at")

    is_shortlisted = False
    if request.user.is_authenticated and hasattr(request.user, "profile"):
        is_shortlisted = freelancer in request.user.profile.saved_freelancers.all()

    context = {
        "freelancer": freelancer,
        "profile": profile,
        "services": services,
        "completed_orders": completed_orders,
        "reviews": reviews,
        "is_shortlisted": is_shortlisted,
    }
    return render(request, "accounts/freelancer_profile.html", context)


def password_reset_request_view(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.filter(email=email).first()
            if user:
                # Console email simulation
                send_mail(
                    subject="SkillSphere Password Reset",
                    message=f"Hello {user.get_display_name()},\n\nPlease use this link to reset your SkillSphere password: http://127.0.0.1:8000/password-reset/confirm/?user={user.username}",
                    from_email="noreply@skillsphere.io",
                    recipient_list=[email],
                    fail_silently=True,
                )
            messages.success(
                request,
                f"Password reset instructions have been dispatched to {email}. (Check server console in development mode).",
            )
            return redirect("accounts:login")
    else:
        form = PasswordResetRequestForm()

    return render(request, "accounts/password_reset_request.html", {"form": form})


def password_reset_confirm_view(request):
    username = request.GET.get("user")
    user = get_object_or_404(User, username=username)

    if request.method == "POST":
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password"]
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password reset successful! Please sign in with your new password.")
            return redirect("accounts:login")
    else:
        form = PasswordResetConfirmForm()

    return render(request, "accounts/password_reset_confirm.html", {"form": form, "reset_user": user})
