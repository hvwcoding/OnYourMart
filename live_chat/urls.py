from django.urls import path
from . import views

urlpatterns = [
    path('start/<int:listing_id>/', views.start_chat, name='start_chat'),
    path('', views.chatroom, name='chatroom_without_id'),
    path('<int:listing_id>/', views.chatroom, name='chatroom'),  # Using the listing_id
    path('unread-messages-count/', views.unread_messages_count, name='unread_messages_count'),
]
