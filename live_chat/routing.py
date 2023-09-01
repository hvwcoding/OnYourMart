from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<listing_id>\d+)/$', consumers.ChatRoomConsumer.as_asgi()),
]
