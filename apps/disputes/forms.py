from django import forms
from .models import Dispute


class DisputeForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ("reason", "description", "evidence_file")
        widgets = {
            "reason": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Provide a factual and detailed explanation of the issue, what was agreed, and why resolution is requested...",
                }
            ),
        }


class DisputeResolutionForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ("status", "resolution_notes")
        widgets = {
            "status": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"
                }
            ),
            "resolution_notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Official findings and resolution determination...",
                }
            ),
        }
