from django.urls import path
from . import views

app_name = "proposals"

urlpatterns = [
    path(
        "projects/<str:project_id>/apply/",
        views.proposal_submit_view,
        name="proposal_submit",
    ),
    path(
        "projects/<str:project_id>/proposals/",
        views.project_proposals_view,
        name="project_proposals",
    ),
    path(
        "proposals/<str:proposal_id>/accept/",
        views.proposal_accept_view,
        name="proposal_accept",
    ),
    path(
        "proposals/<str:proposal_id>/reject/",
        views.proposal_reject_view,
        name="proposal_reject",
    ),
    path(
        "proposals/<str:proposal_id>/withdraw/",
        views.proposal_withdraw_view,
        name="proposal_withdraw",
    ),
]

