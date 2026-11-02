from django.urls import path
from . import views

app_name = "marketplace"

urlpatterns = [
    path("projects/", views.project_list_view, name="project_list"),
    path("projects/create/", views.project_create_view, name="project_create"),
    path(
        "projects/<str:project_id>/",
        views.project_detail_view,
        name="project_detail",
    ),
    path(
        "projects/<str:project_id>/edit/",
        views.project_edit_view,
        name="project_edit",
    ),
    path(
        "projects/<str:project_id>/close/",
        views.project_close_view,
        name="project_close",
    ),
]

