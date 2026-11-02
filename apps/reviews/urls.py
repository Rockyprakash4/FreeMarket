from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("orders/<str:order_id>/review/", views.create_review_view, name="create_review"),
]

