from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from projects.models import Project
from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    MessageSerializer,
    CreateConversationSerializer,
    SendMessageSerializer,
)

User = get_user_model()


class ConversationListView(APIView):
    """
    List user's conversations or start/retrieve an existing negotiation thread.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = (
            Conversation.objects
            .filter(participants=request.user)
            .prefetch_related('participants', 'messages', 'project')
            .order_by('-updated_at')
        )
        serializer = ConversationListSerializer(conversations, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreateConversationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        recipient_id = serializer.validated_data['recipient_id']
        project_id = serializer.validated_data.get('project_id')

        recipient = User.objects.get(id=recipient_id)
        project = Project.objects.filter(id=project_id).first() if project_id else None

        # Check if conversation already exists between these 2 users (optionally for this project)
        qs = Conversation.objects.filter(participants=request.user).filter(participants=recipient)
        if project:
            conversation = qs.filter(project=project).first()
        else:
            conversation = qs.first()

        created = False
        if not conversation:
            conversation = Conversation.objects.create(project=project)
            conversation.participants.add(request.user, recipient)
            created = True

        data = ConversationListSerializer(conversation, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ConversationDetailView(APIView):
    """
    Retrieve single conversation metadata.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        conversation = get_object_or_404(
            Conversation.objects.prefetch_related('participants', 'messages', 'project'),
            id=pk,
            participants=request.user,
        )
        serializer = ConversationListSerializer(conversation, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class MessageListCreateView(APIView):
    """
    List messages in a conversation and send a new message.
    Automatically marks incoming messages as read when listed.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user,
        )

        # Mark unread incoming messages as read
        conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

        messages = conversation.messages.select_related('sender').order_by('created_at')
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user,
        )
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=serializer.validated_data['content'],
        )

        # Touch conversation updated_at so it floats to the top of the chat list
        conversation.save()

        msg_data = MessageSerializer(message, context={'request': request}).data
        return Response(msg_data, status=status.HTTP_201_CREATED)


class MarkMessagesReadView(APIView):
    """
    Mark all unread messages in a conversation as read.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user,
        )
        updated_count = conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        return Response({"status": "success", "marked_read": updated_count}, status=status.HTTP_200_OK)


class TotalUnreadCountView(APIView):
    """
    Get total unread messages count for navbar / tab badge.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_count = (
            Message.objects
            .filter(conversation__participants=request.user, is_read=False)
            .exclude(sender=request.user)
            .count()
        )
        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)
