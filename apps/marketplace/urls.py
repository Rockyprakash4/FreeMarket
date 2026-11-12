from django.urls import path
from . import views

app_name = "marketplace"

urlpatterns = [
    # Projects
    path("projects/", views.project_list_view, name="project_list"),
    path("projects/create/", views.project_create_view, name="project_create"),
    path("projects/<str:project_id>/", views.project_detail_view, name="project_detail"),
    path("projects/<str:project_id>/edit/", views.project_edit_view, name="project_edit"),
    path("projects/<str:project_id>/close/", views.project_close_view, name="project_close"),
    # Services / Gigs
    path("services/", views.service_list_view, name="service_list"),
    path("services/create/", views.service_create_view, name="service_create"),
    path("services/<str:service_id>/", views.service_detail_view, name="service_detail"),
    path("services/<str:service_id>/edit/", views.service_edit_view, name="service_edit"),
    path("services/<str:service_id>/save/", views.saved_service_toggle_view, name="saved_service_toggle"),
    path("saved-services/", views.saved_services_list_view, name="saved_services_list"),
    # AI Estimator API
    path("api/ai/estimate-budget/", views.ai_budget_estimator_api, name="ai_budget_estimator_api"),
]
