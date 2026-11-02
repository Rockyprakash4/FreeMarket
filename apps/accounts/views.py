from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import User, Profile
from .forms import (
    DevMarketRegistrationForm,
    DevMarketLoginForm,
    UserProfileForm,
    FreelancerProfileForm,
)
from reviews.models import Review
from orders.models import Order


def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = DevMarketRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome to DevMarket, {user.first_name or user.username}! Your account has been created.",
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
        form = DevMarketRegistrationForm(initial={"role": initial_role})

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = DevMarketLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_display_name()}!")
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("core:dashboard")
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = DevMarketLoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("core:home")


@login_required
def profile_edit_view(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)
        profile_form = FreelancerProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("accounts:profile_edit")
        else:
            messages.error(
                request, "Please check the form for errors and try again."
            )
    else:
        user_form = UserProfileForm(instance=user)
        profile_form = FreelancerProfileForm(instance=profile)

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "profile": profile,
    }
    return render(request, "accounts/profile_edit.html", context)


def freelancer_list_view(request):
    freelancers = (
        User.objects.filter(role=User.Role.FREELANCER, is_active=True)
        .select_related("profile")
        .order_by("-profile__rating", "-created_at")
    )

    # Search & filters
    query = request.GET.get("q", "").strip()
    skill_filter = request.GET.get("skill", "").strip()
    exp_filter = request.GET.get("experience", "").strip()
    avail_filter = request.GET.get("availability", "").strip()

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

    paginator = Paginator(freelancers, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "query": query,
        "skill_filter": skill_filter,
        "exp_filter": exp_filter,
        "avail_filter": avail_filter,
        "total_count": paginator.count,
    }
    return render(request, "accounts/freelancer_list.html", context)


def freelancer_profile_view(request, username):
    freelancer = get_object_or_404(User, username=username, role=User.Role.FREELANCER)
    profile, _ = Profile.objects.get_or_create(user=freelancer)
    completed_orders = Order.objects.filter(
        freelancer=freelancer, status=Order.Status.COMPLETED
    ).order_by("-completed_at")[:5]
    reviews = Review.objects.filter(reviewee=freelancer).order_by("-created_at")

    context = {
        "freelancer": freelancer,
        "profile": profile,
        "completed_orders": completed_orders,
        "reviews": reviews,
    }
    return render(request, "accounts/freelancer_profile.html", context)
