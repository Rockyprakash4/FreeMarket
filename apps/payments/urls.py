from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("payments/", views.payment_list_view, name="payment_list"),
]

