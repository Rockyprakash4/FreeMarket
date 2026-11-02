from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("notifications/", views.notification_list_view, name="notification_list"),
    path(
        "notifications/<str:notification_id>/read/",
        views.mark_as_read_view,
        name="mark_as_read",
    ),
    path(
        "notifications/mark-all-read/",
        views.mark_all_read_view,
        name="mark_all_read",
    ),
]

