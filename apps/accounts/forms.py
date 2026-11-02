from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class DevMarketRegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            (User.Role.FREELANCER, "Freelancer / Developer — I want to find work"),
            (User.Role.CLIENT, "Client / Project Owner — I want to hire talent"),
        ],
        widget=forms.RadioSelect(
            attrs={"class": "text-brand-600 focus:ring-brand-500"}
        ),
        initial=User.Role.FREELANCER,
        label="I am joining as a",
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-sm",
                "placeholder": "you@example.com",
            }
        ),
    )
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-sm",
                "placeholder": "First Name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-sm",
                "placeholder": "Last Name",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-sm",
                "placeholder": "Choose a username",
            }
        )
        self.fields["password1"].widget.attrs.update(
            {
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-sm",
                "placeholder": "At least 8 characters",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-sm",
                "placeholder": "Confirm password",
            }
        )


class DevMarketLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-sm",
                "placeholder": "Username",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 text-sm",
                "placeholder": "••••••••",
            }
        )
    )


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"
            }
        ),
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"
            }
        ),
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                "placeholder": "+1 (555) 000-0000",
            }
        ),
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                "placeholder": "e.g. San Francisco, CA or Remote",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "location", "avatar")


class FreelancerProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "headline",
            "bio",
            "skills",
            "experience_level",
            "hourly_rate",
            "availability",
            "portfolio_website",
            "github_url",
            "linkedin_url",
        )
        widgets = {
            "headline": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "e.g. Senior Full-Stack Python & React Engineer",
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Tell clients about your background, experience, and the problems you solve...",
                }
            ),
            "skills": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "Python, Django, React, Tailwind, PostgreSQL, MongoDB, Docker",
                }
            ),
            "experience_level": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"
                }
            ),
            "hourly_rate": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "50.00",
                }
            ),
            "availability": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm"
                }
            ),
            "portfolio_website": forms.URLInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "https://yourportfolio.dev",
                }
            ),
            "github_url": forms.URLInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "https://github.com/username",
                }
            ),
            "linkedin_url": forms.URLInput(
                attrs={
                    "class": "w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-brand-500 text-sm",
                    "placeholder": "https://linkedin.com/in/username",
                }
            ),
        }

