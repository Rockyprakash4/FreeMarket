from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Project, Category
from .forms import ProjectForm
from proposals.models import Proposal
from proposals.forms import ProposalForm


def project_list_view(request):
    projects = (
        Project.objects.filter(status=Project.Status.OPEN)
        .select_related("client", "category")
        .order_by("-created_at")
    )
    categories = Category.objects.all()

    # Filters
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()
    skill_filter = request.GET.get("skill", "").strip()
    project_type = request.GET.get("type", "").strip()
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

    # Increment views count
    Project.objects.filter(id=project_id).update(views_count=project.views_count + 1)

    user_proposal = None
    proposal_form = None
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

    context = {
        "project": project,
        "user_proposal": user_proposal,
        "proposal_form": proposal_form,
        "is_owner": request.user.is_authenticated and project.client == request.user,
    }
    return render(request, "marketplace/project_detail.html", context)


@login_required
def project_create_view(request):
    if request.user.role != request.user.Role.CLIENT and not request.user.is_superuser:
        messages.error(
            request,
            "Only clients can post new projects. If you wish to hire talent, please switch or update your role.",
        )
        return redirect("marketplace:project_list")

    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.client = request.user
            project.status = Project.Status.OPEN
            project.save()
            messages.success(
                request,
                f"Your project '{project.title}' is now live and accepting proposals!",
            )
            return redirect("marketplace:project_detail", project_id=project.id)
        else:
            messages.error(
                request, "Please check the highlighted errors and try again."
            )
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
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project details updated successfully.")
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
