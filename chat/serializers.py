from rest_framework import serializers
from django.contrib.auth import get_user_model
from projects.models import Project
from .models import Conversation, Message

User = get_user_model()


class ParticipantSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    avatar_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'display_name', 'avatar_display']

    def get_display_name(self, obj):
        if hasattr(obj, 'profile') and obj.profile.name:
            return obj.profile.name
        first_last = f"{obj.first_name} {obj.last_name}".strip()
        return first_last or obj.username

    def get_avatar_display(self, obj):
        if hasattr(obj, 'profile'):
            if obj.profile.avatar:
                request = self.context.get('request')
                return request.build_absolute_uri(obj.profile.avatar.url) if request else obj.profile.avatar.url
            if obj.profile.avatar_url:
                return obj.profile.avatar_url
        if hasattr(obj, 'google_profile') and obj.google_profile.picture:
            return obj.google_profile.picture
        return None


class ChatProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'status']


class MessageSerializer(serializers.ModelSerializer):
    sender = ParticipantSerializer(read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'is_read', 'is_mine', 'created_at']
        read_only_fields = ['id', 'conversation', 'sender', 'is_mine', 'created_at']

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender_id == request.user.id
        return False


class ConversationListSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    project = ChatProjectSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'other_participant',
            'project',
            'last_message',
            'unread_count',
            'updated_at',
            'created_at',
        ]

    def get_other_participant(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        other = obj.participants.exclude(id=request.user.id).first()
        if other:
            return ParticipantSerializer(other, context=self.context).data
        current = obj.participants.filter(id=request.user.id).first()
        return ParticipantSerializer(current, context=self.context).data if current else None

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        if last:
            return {
                'id': last.id,
                'content': last.content,
                'sender_id': last.sender_id,
                'created_at': last.created_at,
                'is_read': last.is_read,
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=request.user).count()


class CreateConversationSerializer(serializers.Serializer):
    recipient_id = serializers.IntegerField(required=True)
    project_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_recipient_id(self, value):
        if not User.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Recipient user does not exist or is inactive.")
        return value

    def validate_project_id(self, value):
        if value is not None and not Project.objects.filter(id=value).exists():
            raise serializers.ValidationError("Project does not exist.")
        return value


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(required=True, allow_blank=False, max_length=5000)

    def validate_content(self, value):
        clean = value.strip()
        if not clean:
            raise serializers.ValidationError("Message content cannot be blank.")
        return clean
