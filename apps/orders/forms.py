from django import forms
from .models import Order


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

