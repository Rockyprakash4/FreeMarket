from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("messages/", views.conversation_list_view, name="conversation_list"),
    path(
        "messages/<str:conversation_id>/",
        views.conversation_detail_view,
        name="conversation_detail",
    ),
    path(
        "messages/start/<str:username>/",
        views.start_conversation_view,
        name="start_conversation",
    ),
]

