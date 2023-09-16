from django.db import models

from user.models import CustomUser
from django.db.models import Q
from listing.models import Listing


class ChatRoomManager(models.Manager):
    def get_or_create_chat(self, user1, user2, listing):
        chat_room = ChatRoom.objects.filter(
            Q(participant1=user1, participant2=user2, listing=listing) |
            Q(participant1=user2, participant2=user1, listing=listing)
        ).first()

        if not chat_room:
            chat_room = ChatRoom.objects.create(participant1=user1, participant2=user2, listing=listing)

        return chat_room


class ChatRoom(models.Model):
    participant1 = models.ForeignKey(CustomUser, related_name='chatroom_participant1', on_delete=models.CASCADE)
    participant2 = models.ForeignKey(CustomUser, related_name='chatroom_participant2', on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = ChatRoomManager()

    class Meta:
        unique_together = ('participant1', 'participant2', 'listing')


class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
