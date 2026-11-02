from django import forms
from .models import Project, Category


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
            "budget",
            "project_type",
            "deadline",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "e.g. Build a Modern Next.js Dashboard with Stripe & Auth",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"
                }
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
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"
                }
            ),
        }

