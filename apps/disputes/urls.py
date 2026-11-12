from django.urls import path
from . import views

app_name = "disputes"

urlpatterns = [
    path("disputes/", views.dispute_list_view, name="dispute_list"),
    path("orders/<str:order_id>/dispute/", views.open_dispute_view, name="open_dispute"),
    path("disputes/<str:dispute_id>/", views.dispute_detail_view, name="dispute_detail"),
    path("disputes/<str:dispute_id>/resolve/", views.admin_resolve_dispute_view, name="admin_resolve_dispute"),
]
