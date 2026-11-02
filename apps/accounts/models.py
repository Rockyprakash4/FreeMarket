from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "client", "Client / Project Owner"
        FREELANCER = "freelancer", "Freelancer / Developer"
        ADMIN = "admin", "Administrator"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.FREELANCER,
        help_text="Primary platform role",
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT or self.is_superuser

    @property
    def is_freelancer(self):
        return self.role == self.Role.FREELANCER

    def get_display_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username


class Profile(models.Model):
    class ExperienceLevel(models.TextChoices):
        ENTRY = "entry", "Entry Level"
        INTERMEDIATE = "intermediate", "Intermediate"
        EXPERT = "expert", "Expert / Senior"

    class Availability(models.TextChoices):
        FULL_TIME = "full_time", "Available Full-Time (40 hrs/wk)"
        PART_TIME = "part_time", "Available Part-Time (20 hrs/wk)"
        BUSY = "busy", "Not Available Currently"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    headline = models.CharField(
        max_length=140,
        blank=True,
        default="",
        help_text="e.g. Senior Full-Stack Python & React Developer",
    )
    bio = models.TextField(blank=True, default="")
    skills = models.TextField(
        blank=True,
        default="",
        help_text="Comma-separated list of skills (e.g. Python, Django, React, MongoDB)",
    )
    experience_level = models.CharField(
        max_length=20,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.INTERMEDIATE,
    )
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, help_text="USD hourly rate"
    )
    availability = models.CharField(
        max_length=20,
        choices=Availability.choices,
        default=Availability.FULL_TIME,
    )
    portfolio_website = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    rating = models.FloatField(default=0.0)
    reviews_count = models.PositiveIntegerField(default=0)
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_skills_list(self):
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(",") if s.strip()]


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, "profile"):
            instance.profile.save()
        else:
            Profile.objects.create(user=instance)
