from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("reviews/", views.review_list_view, name="review_list"),
    path("orders/<str:order_id>/review/", views.create_review_view, name="create_review"),
    path("reviews/<str:review_id>/report/", views.report_review_view, name="report_review"),
]
