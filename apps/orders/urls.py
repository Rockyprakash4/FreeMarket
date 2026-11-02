from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("orders/", views.order_list_view, name="order_list"),
    path("orders/<str:order_id>/", views.order_detail_view, name="order_detail"),
    path(
        "orders/<str:order_id>/deliver/",
        views.order_deliver_view,
        name="order_deliver",
    ),
    path(
        "orders/<str:order_id>/approve/",
        views.order_approve_view,
        name="order_approve",
    ),
]

