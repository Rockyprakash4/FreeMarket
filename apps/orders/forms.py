from django import forms
from .models import Order, Milestone


class DeliverySubmissionForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("delivery_url", "delivery_notes", "delivery_file")
        widgets = {
            "delivery_url": forms.URLInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "https://github.com/user/project or live demo link",
                }
            ),
            "delivery_notes": forms.Textarea(
                attrs={
                    "rows": 5,
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Summarize what was built, testing performed, installation instructions, and notes for the client...",
                }
            ),
        }


class RevisionRequestForm(forms.Form):
    notes = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                "placeholder": "Explain specific changes, bug fixes, or adjustments required before approval...",
            }
        ),
        label="Revision Requirements",
        help_text="Be clear and specific so the freelancer can address your feedback.",
    )


class MilestoneForm(forms.ModelForm):
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-xs",
            }
        ),
    )

    class Meta:
        model = Milestone
        fields = ("title", "description", "amount", "due_date")
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-xs",
                    "placeholder": "e.g. Milestone 1: Database Schema & Authentication",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-xs",
                    "placeholder": "Deliverables included in this milestone...",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-xs",
                    "placeholder": "100.00",
                }
            ),
        }


class MilestoneSubmissionForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ("deliverable_url", "submission_notes", "deliverable_file")
        widgets = {
            "deliverable_url": forms.URLInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "https://github.com/... or PR link",
                }
            ),
            "submission_notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Milestone delivery overview...",
                }
            ),
        }
