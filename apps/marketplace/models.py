from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    icon = models.CharField(
        max_length=50,
        default="code",
        help_text="Icon identifier e.g. code, cpu, cloud, smartphone, palette, shield",
    )
    is_featured = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Project(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open for Proposals"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CLOSED = "closed", "Closed"

    class ProjectType(models.TextChoices):
        FIXED = "fixed", "Fixed Price"
        HOURLY = "hourly", "Hourly Rate"

    class Complexity(models.TextChoices):
        ENTRY = "entry", "Entry (Standard)"
        INTERMEDIATE = "intermediate", "Intermediate (Custom Logic)"
        EXPERT = "expert", "Expert (High Architecture / Scale)"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects_posted",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    required_skills = models.TextField(
        help_text="Comma-separated required skills e.g. Python, Django, React, MongoDB"
    )
    budget = models.DecimalField(
        max_digits=10, decimal_places=2, default=100.00, help_text="Budget in USD"
    )
    deadline = models.DateField(null=True, blank=True)
    project_type = models.CharField(
        max_length=20, choices=ProjectType.choices, default=ProjectType.FIXED
    )
    complexity = models.CharField(
        max_length=20, choices=Complexity.choices, default=Complexity.INTERMEDIATE
    )
    attachment = models.FileField(
        upload_to="project_attachments/", blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_skills_list(self):
        if not self.required_skills:
            return []
        return [s.strip() for s in self.required_skills.split(",") if s.strip()]

    @property
    def proposals_count(self):
        return self.proposals.count()

    @property
    def is_open(self):
        return self.status == self.Status.OPEN


class Service(models.Model):
    """
    Freelance Service / Gig offered directly by a developer.
    Clients can purchase services or add them to their wishlist.
    """
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="services_offered",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
    )
    title = models.CharField(
        max_length=200,
        help_text="e.g. I will build a production-ready Django REST API with JWT Auth",
    )
    description = models.TextField(
        help_text="Detailed description of what deliverables and revisions are included"
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=150.00, help_text="Price in USD"
    )
    delivery_time_days = models.PositiveIntegerField(
        default=3, help_text="Expected delivery time in days"
    )
    technologies = models.CharField(
        max_length=255,
        help_text="Comma-separated technologies (e.g. Django, Python, PostgreSQL, Docker)",
    )
    image = models.ImageField(upload_to="services/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_tech_list(self):
        if not self.technologies:
            return []
        return [t.strip() for t in self.technologies.split(",") if t.strip()]


class SavedService(models.Model):
    """Client wishlist / bookmark for freelancer services."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_services",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="saved_by_users",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "service"],
                name="unique_saved_service_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.service.title}"
