from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Conversation, Message
from marketplace.models import Project
from accounts.models import User
from notifications.models import Notification


@login_required
def conversation_list_view(request):
    conversations = (
        request.user.conversations.all()
        .prefetch_related("participants", "messages")
        .select_related("project")
        .order_by("-updated_at")
    )
    return render(
        request,
        "messaging/conversation_list.html",
        {"conversations": conversations},
    )


@login_required
def conversation_detail_view(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related("participants", "messages__sender"),
        id=conversation_id,
    )

    if request.user not in conversation.participants.all() and not request.user.is_superuser:
        messages.error(request, "You do not have access to this conversation.")
        return redirect("messaging:conversation_list")

    # Mark incoming messages as read
    conversation.messages.exclude(sender=request.user).filter(is_read=False).update(
        is_read=True
    )

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        attachment = request.FILES.get("attachment")

        if content or attachment:
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content or "(File attached)",
                attachment=attachment,
            )
            conversation.save()

            other_user = conversation.get_other_participant(request.user)
            if other_user:
                Notification.objects.create(
                    recipient=other_user,
                    title="New Direct Message",
                    message=f"{request.user.get_display_name()}: {(content or 'Attached a file')[:80]}",
                    link_url=f"/messages/{conversation.id}/",
                    notification_type=Notification.NotificationType.NEW_MESSAGE,
                )

            return redirect("messaging:conversation_detail", conversation_id=conversation.id)

    other_user = conversation.get_other_participant(request.user)
    messages_list = conversation.messages.all()

    context = {
        "conversation": conversation,
        "other_user": other_user,
        "messages_list": messages_list,
    }
    return render(request, "messaging/conversation_detail.html", context)


@login_required
def start_conversation_view(request, username):
    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        messages.warning(request, "You cannot message yourself.")
        return redirect("core:dashboard")

    project_id = request.GET.get("project_id")
    project = None
    if project_id:
        project = Project.objects.filter(id=project_id).first()

    conversation = (
        Conversation.objects.filter(participants=request.user)
        .filter(participants=other_user)
        .first()
    )

    if not conversation:
        conversation = Conversation.objects.create(project=project)
        conversation.participants.add(request.user, other_user)

    return redirect("messaging:conversation_detail", conversation_id=conversation.id)
