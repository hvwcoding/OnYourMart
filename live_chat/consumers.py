import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.listing_id = self.scope['url_route']['kwargs']['listing_id']
        self.room_group_name = f'chat_{self.listing_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        sender_email_prefix = await self.get_sender_email_prefix(self.scope['user'])

        # Save message to DB
        await self._save_message_to_db(message, self.scope['user'])

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': f"{sender_email_prefix}: {message}"
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    @database_sync_to_async
    def get_sender_email_prefix(self, user):
        return user.email.split('@')[0]

    @database_sync_to_async
    def _save_message_to_db(self, message_text, sender):
        from .models import ChatRoom, Message
        chat_room = ChatRoom.objects.get(listing_id=self.listing_id)
        message = Message(chat_room=chat_room, content=message_text, sender=sender)
        message.save()

    @database_sync_to_async
    def get_last_messages_from_db(self, chat_room):
        from .models import Message
        return list(Message.objects.filter(chat_room=chat_room).order_by('timestamp')[:50])
