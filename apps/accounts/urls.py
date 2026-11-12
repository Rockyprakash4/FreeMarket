from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("profile/verify/", views.submit_verification_view, name="submit_verification"),
    path("profile/verify-email/", views.verify_email_view, name="verify_email"),
    path("password-reset/", views.password_reset_request_view, name="password_reset"),
    path("password-reset/confirm/", views.password_reset_confirm_view, name="password_reset_confirm"),
    path("freelancers/", views.freelancer_list_view, name="freelancer_list"),
    path("freelancers/<str:username>/", views.freelancer_profile_view, name="freelancer_profile"),
    path("freelancers/<str:username>/shortlist/", views.shortlist_toggle_view, name="shortlist_toggle"),
]
