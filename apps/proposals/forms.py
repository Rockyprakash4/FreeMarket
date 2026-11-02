from django import forms
from .models import Proposal


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ("proposed_price", "estimated_delivery_days", "cover_letter")
        widgets = {
            "proposed_price": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Your total bid in USD",
                }
            ),
            "estimated_delivery_days": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Days to deliver (e.g. 7)",
                }
            ),
            "cover_letter": forms.Textarea(
                attrs={
                    "rows": 5,
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Explain how you will approach this project, relevant past experience, and why you are the best person for the job...",
                }
            ),
        }

