from django.urls import path
from . import views

urlpatterns = [
    path("conversations/", views.ConversationListView.as_view(), name="chat-conversations"),
    path("conversations/<int:pk>/", views.ConversationDetailView.as_view(), name="chat-conversation-detail"),
    path("conversations/<int:conversation_id>/messages/", views.MessageListCreateView.as_view(), name="chat-messages"),
    path("conversations/<int:conversation_id>/read/", views.MarkMessagesReadView.as_view(), name="chat-mark-read"),
    path("unread-count/", views.TotalUnreadCountView.as_view(), name="chat-unread-count"),
]
