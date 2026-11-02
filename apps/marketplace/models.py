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
        help_text="Icon identifier e.g. code, design, mobile, ai, web, devops",
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
