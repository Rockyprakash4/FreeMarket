from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("freelancers/", views.freelancer_list_view, name="freelancer_list"),
    path(
        "freelancers/<str:username>/",
        views.freelancer_profile_view,
        name="freelancer_profile",
    ),
]

