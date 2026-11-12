from django import forms
from .models import Project, Category, Service


class ProjectForm(forms.ModelForm):
    deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
            }
        ),
    )

    class Meta:
        model = Project
        fields = (
            "title",
            "category",
            "description",
            "required_skills",
            "complexity",
            "budget",
            "project_type",
            "deadline",
            "attachment",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "e.g. Build an AI-Enabled Analytics Dashboard in Next.js & Django",
                }
            ),
            "category": forms.Select(
                attrs={"class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"}
            ),
            "complexity": forms.Select(
                attrs={"class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"}
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Provide a comprehensive overview of requirements, deliverables, technical stack expectations, and acceptance criteria...",
                }
            ),
            "required_skills": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "e.g. React, Django, Python, Tailwind, REST API",
                }
            ),
            "budget": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "500.00",
                }
            ),
            "project_type": forms.Select(
                attrs={"class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"}
            ),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = (
            "title",
            "category",
            "description",
            "price",
            "delivery_time_days",
            "technologies",
            "image",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "e.g. I will build a scalable microservices architecture in Python & Docker",
                }
            ),
            "category": forms.Select(
                attrs={"class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"}
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Detail your service scope, deliverables, technologies utilized, and what you need from the client...",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "150.00",
                }
            ),
            "delivery_time_days": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "3",
                }
            ),
            "technologies": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "e.g. Django, Python, Docker, Celery, Redis",
                }
            ),
        }
