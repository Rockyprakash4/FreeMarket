from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("orders/", views.order_list_view, name="order_list"),
    path("orders/<str:order_id>/", views.order_detail_view, name="order_detail"),
    path("orders/<str:order_id>/deliver/", views.order_deliver_view, name="order_deliver"),
    path("orders/<str:order_id>/revision/", views.order_request_revision_view, name="order_request_revision"),
    path("orders/<str:order_id>/approve/", views.order_approve_view, name="order_approve"),
    path("orders/order-service/<str:service_id>/", views.order_create_from_service_view, name="order_create_from_service"),
    # Milestones
    path("orders/<str:order_id>/milestones/create/", views.milestone_create_view, name="milestone_create"),
    path("milestones/<str:milestone_id>/submit/", views.milestone_submit_view, name="milestone_submit"),
    path("milestones/<str:milestone_id>/approve/", views.milestone_approve_view, name="milestone_approve"),
]
