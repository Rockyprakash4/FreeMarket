from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Project, Category, Service, SavedService
from .forms import ProjectForm, ServiceForm
from proposals.models import Proposal
from proposals.forms import ProposalForm
from core.ai_engine import match_freelancers_for_project, estimate_project_budget_and_timeline


def project_list_view(request):
    projects = (
        Project.objects.filter(status=Project.Status.OPEN)
        .select_related("client", "category")
        .order_by("-created_at")
    )
    categories = Category.objects.all()

    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()
    skill_filter = request.GET.get("skill", "").strip()
    project_type = request.GET.get("type", "").strip()
    complexity = request.GET.get("complexity", "").strip()
    min_budget = request.GET.get("min_budget", "").strip()
    max_budget = request.GET.get("max_budget", "").strip()
    sort_by = request.GET.get("sort", "newest").strip()

    if query:
        projects = projects.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(required_skills__icontains=query)
        )
    if category_slug:
        projects = projects.filter(category__slug=category_slug)
    if skill_filter:
        projects = projects.filter(required_skills__icontains=skill_filter)
    if project_type:
        projects = projects.filter(project_type=project_type)
    if complexity:
        projects = projects.filter(complexity=complexity)
    if min_budget:
        try:
            projects = projects.filter(budget__gte=float(min_budget))
        except ValueError:
            pass
    if max_budget:
        try:
            projects = projects.filter(budget__lte=float(max_budget))
        except ValueError:
            pass

    if sort_by == "budget_desc":
        projects = projects.order_by("-budget")
    elif sort_by == "budget_asc":
        projects = projects.order_by("budget")
    else:
        projects = projects.order_by("-created_at")

    paginator = Paginator(projects, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "selected_category": category_slug,
        "query": query,
        "skill_filter": skill_filter,
        "project_type": project_type,
        "complexity": complexity,
        "min_budget": min_budget,
        "max_budget": max_budget,
        "sort_by": sort_by,
        "total_count": paginator.count,
    }
    return render(request, "marketplace/project_list.html", context)


def project_detail_view(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("client", "category"), id=project_id
    )

    Project.objects.filter(id=project_id).update(views_count=project.views_count + 1)

    user_proposal = None
    proposal_form = None
    is_owner = request.user.is_authenticated and project.client == request.user
    ai_recommendations = []

    if request.user.is_authenticated:
        if request.user.role == request.user.Role.FREELANCER:
            user_proposal = Proposal.objects.filter(
                project=project, freelancer=request.user
            ).first()
            if not user_proposal and project.is_open:
                proposal_form = ProposalForm(
                    initial={
                        "proposed_price": project.budget,
                        "estimated_delivery_days": 7,
                    }
                )
        elif is_owner:
            # Generate AI Candidate Recommendations for Owner
            ai_recommendations = match_freelancers_for_project(project, top_k=4)

    context = {
        "project": project,
        "user_proposal": user_proposal,
        "proposal_form": proposal_form,
        "is_owner": is_owner,
        "ai_recommendations": ai_recommendations,
    }
    return render(request, "marketplace/project_detail.html", context)


@login_required
def project_create_view(request):
    if request.user.role != request.user.Role.CLIENT and not request.user.is_superuser:
        messages.error(
            request, "Only client accounts can post projects. Please sign in as a client to post."
        )
        return redirect("marketplace:project_list")

    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.client = request.user
            project.status = Project.Status.OPEN
            project.save()
            messages.success(
                request,
                f"Your project '{project.title}' is now live and accepting applications!",
            )
            return redirect("marketplace:project_detail", project_id=project.id)
        else:
            messages.error(request, "Please check the highlighted form errors and try again.")
    else:
        form = ProjectForm()

    return render(request, "marketplace/project_form.html", {"form": form, "action": "Create"})


@login_required
def project_edit_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, client=request.user)

    if project.status not in [Project.Status.OPEN]:
        messages.warning(
            request, "You cannot edit a project that is already in progress or completed."
        )
        return redirect("marketplace:project_detail", project_id=project.id)

    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project specifications updated successfully.")
            return redirect("marketplace:project_detail", project_id=project.id)
        else:
            messages.error(request, "Please check the form for errors.")
    else:
        form = ProjectForm(instance=project)

    return render(
        request,
        "marketplace/project_form.html",
        {"form": form, "project": project, "action": "Edit"},
    )


@login_required
def project_close_view(request, project_id):
    project = get_object_or_404(Project, id=project_id, client=request.user)
    if request.method == "POST":
        if project.status == Project.Status.OPEN:
            project.status = Project.Status.CLOSED
            project.save()
            messages.info(request, f"Project '{project.title}' has been closed.")
        else:
            messages.warning(request, "This project cannot be closed in its current state.")
        return redirect("marketplace:project_detail", project_id=project.id)
    return render(request, "marketplace/project_confirm_close.html", {"project": project})


# --- FREELANCE SERVICES / GIGS WORKFLOW ---

def service_list_view(request):
    services = (
        Service.objects.filter(is_active=True)
        .select_related("freelancer", "freelancer__profile", "category")
        .order_by("-created_at")
    )
    categories = Category.objects.all()

    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()
    tech_filter = request.GET.get("tech", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    max_days = request.GET.get("max_days", "").strip()

    if query:
        services = services.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(technologies__icontains=query)
        )
    if category_slug:
        services = services.filter(category__slug=category_slug)
    if tech_filter:
        services = services.filter(technologies__icontains=tech_filter)
    if max_price:
        try:
            services = services.filter(price__lte=float(max_price))
        except ValueError:
            pass
    if max_days:
        try:
            services = services.filter(delivery_time_days__lte=int(max_days))
        except ValueError:
            pass

    paginator = Paginator(services, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    saved_service_ids = set()
    if request.user.is_authenticated:
        saved_service_ids = set(
            SavedService.objects.filter(user=request.user).values_list("service_id", flat=True)
        )

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "selected_category": category_slug,
        "query": query,
        "tech_filter": tech_filter,
        "max_price": max_price,
        "max_days": max_days,
        "saved_service_ids": saved_service_ids,
        "total_count": paginator.count,
    }
    return render(request, "marketplace/service_list.html", context)


def service_detail_view(request, service_id):
    service = get_object_or_404(
        Service.objects.select_related("freelancer", "freelancer__profile", "category"),
        id=service_id,
    )
    Service.objects.filter(id=service_id).update(views_count=service.views_count + 1)

    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedService.objects.filter(user=request.user, service=service).exists()

    other_services = Service.objects.filter(
        freelancer=service.freelancer, is_active=True
    ).exclude(id=service.id)[:3]

    context = {
        "service": service,
        "is_saved": is_saved,
        "other_services": other_services,
        "is_seller": request.user.is_authenticated and service.freelancer == request.user,
    }
    return render(request, "marketplace/service_detail.html", context)


@login_required
def service_create_view(request):
    if request.user.role != request.user.Role.FREELANCER and not request.user.is_superuser:
        messages.error(request, "Only freelancers can publish service packages.")
        return redirect("marketplace:service_list")

    if request.method == "POST":
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.freelancer = request.user
            service.save()
            messages.success(request, f"Service '{service.title}' is now live in the catalog!")
            return redirect("marketplace:service_detail", service_id=service.id)
        else:
            messages.error(request, "Please check form errors.")
    else:
        form = ServiceForm()

    return render(request, "marketplace/service_form.html", {"form": form, "action": "Publish"})


@login_required
def service_edit_view(request, service_id):
    service = get_object_or_404(Service, id=service_id, freelancer=request.user)

    if request.method == "POST":
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service updated successfully.")
            return redirect("marketplace:service_detail", service_id=service.id)
        else:
            messages.error(request, "Please check form errors.")
    else:
        form = ServiceForm(instance=service)

    return render(
        request,
        "marketplace/service_form.html",
        {"form": form, "service": service, "action": "Edit"},
    )


@login_required
def saved_service_toggle_view(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    saved = SavedService.objects.filter(user=request.user, service=service).first()
    if saved:
        saved.delete()
        messages.info(request, f"Removed '{service.title}' from your saved wishlist.")
    else:
        SavedService.objects.create(user=request.user, service=service)
        messages.success(request, f"Saved '{service.title}' to your wishlist!")

    return redirect(request.META.get("HTTP_REFERER", "marketplace:service_list"))


@login_required
def saved_services_list_view(request):
    saved_items = (
        SavedService.objects.filter(user=request.user)
        .select_related("service", "service__freelancer", "service__category")
        .order_by("-created_at")
    )
    return render(request, "marketplace/saved_services.html", {"saved_items": saved_items})


def ai_budget_estimator_api(request):
    """Real-time JSON endpoint for Smart Project Budget Estimator."""
    desc = request.GET.get("description", "")
    cat = request.GET.get("category", "")
    skills = [s.strip() for s in request.GET.get("skills", "").split(",") if s.strip()]
    comp = request.GET.get("complexity", "intermediate")

    result = estimate_project_budget_and_timeline(desc, cat, skills, comp)
    return JsonResponse(
        {
            "min_budget": float(result["min_budget"]),
            "max_budget": float(result["max_budget"]),
            "recommended_budget": float(result["recommended_budget"]),
            "min_days": result["min_days"],
            "max_days": result["max_days"],
            "recommended_days": result["recommended_days"],
            "factors": result["factors"],
        }
    )
