from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.shortcuts import render, redirect, get_object_or_404

from .models import ChatRoom

from listing.models import Listing

from django.http import JsonResponse
from .models import Message

import logging

logger = logging.getLogger(__name__)


@login_required
def start_chat(request, listing_id):
    current_user = request.user
    listing = get_object_or_404(Listing, id=listing_id)
    receiver = listing.user
    chat_room = ChatRoom.objects.get_or_create_chat(current_user, receiver, listing)
    return redirect('chatroom', listing_id=listing.id)


def chatroom(request, listing_id=None):
    current_user = request.user
    recent_messages = []

    # Fetch all chatrooms for the user
    chat_rooms = ChatRoom.objects.filter(Q(participant1=current_user) | Q(participant2=current_user))
    chat_rooms = chat_rooms.annotate(last_message_timestamp=Max('messages__timestamp')).order_by(
        '-last_message_timestamp')

    chat_rooms = ChatRoom.objects.filter(
        Q(participant1=current_user) | Q(participant2=current_user)
    ).select_related('participant1', 'participant2', 'listing')  # TODO: this is a hack to avoid N+1 queries

    for chat_room in chat_rooms:
        # Identify the 'other_user' for each chat_room
        other_user = chat_room.participant1 if chat_room.participant2 == current_user else chat_room.participant2
        chat_room.other_user = other_user
        chat_room.other_user_prefix = other_user.email.split('@')[0]

        # Set avatar flag
        try:
            if other_user.avatar and hasattr(other_user.avatar, 'file') and other_user.avatar.file:
                chat_room.has_avatar = True
                chat_room.other_user_avatar_url = other_user.avatar.url
            else:
                chat_room.has_avatar = False
        except ValueError:
            chat_room.has_avatar = False

    # If a listing_id is provided, fetch the specific chatroom for that listing
    active_chat_room = None
    if listing_id:
        try:
            active_chat_room = ChatRoom.objects.get(Q(participant1=current_user) | Q(participant2=current_user),
                                                    listing_id=listing_id)
            other_user = active_chat_room.participant1 if active_chat_room.participant2 == current_user else active_chat_room.participant2
            active_chat_room.other_user_prefix = other_user.email.split('@')[0]

            # Fetch the last N messages for the active_chat_room
            recent_messages = Message.objects.filter(chat_room=active_chat_room).order_by('timestamp')[:50]

            # Mark unread messages in the active chat room as read
            mark_messages_as_read(active_chat_room.id)

        except ChatRoom.DoesNotExist:
            logger.error(f"Chat does not exist for listing {listing_id}")
            messages.error(request, "Chat does not exist!")
            return redirect('chatroom_without_id')  # Redirect to chatroom without ID if chat doesn't exist

    context = {
        'chat_rooms': chat_rooms,
        'active_chat_room': active_chat_room,
        'current_user': current_user,
        'current_user_prefix': current_user.email.split('@')[0],
        'recent_messages': recent_messages  # Adding recent messages to the context
    }

    return render(request, 'chatroom.html', context)


@login_required
def unread_messages_count(request):
    count = Message.objects.filter(
        chat_room__in=ChatRoom.objects.filter(Q(participant1=request.user) | Q(participant2=request.user)),
        is_read=False).exclude(sender=request.user).count()
    return JsonResponse({"unread_count": count})


def mark_messages_as_read(chat_room):
    try:
        chat_room = ChatRoom.objects.get(id=chat_room)
        Message.objects.filter(chat_room=chat_room, is_read=False).update(is_read=True)
    except ChatRoom.DoesNotExist:
        logger.error(f"Attempted to mark messages as read for chat room {chat_room} which does not exist.")
        return
