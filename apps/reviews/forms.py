from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(5, "★★★★★ (5 - Excellent)"), (4, "★★★★☆ (4 - Very Good)"), (3, "★★★☆☆ (3 - Good)"), (2, "★★☆☆☆ (2 - Fair)"), (1, "★☆☆☆☆ (1 - Poor)")],
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"
            }
        ),
        label="Overall Rating",
    )

    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Describe your experience working together, communication, delivery quality, and recommendations...",
                }
            )
        }

