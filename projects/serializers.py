from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Project, Skill, ProjectMember

User = get_user_model()


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']


class ProjectMemberUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = ProjectMemberUserSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'joined_at']


class ProjectSerializer(serializers.ModelSerializer):
    skills = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.all(),
        required=False,
    )
    remaining_capacity = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'goal',
            'description',
            'creator',
            'capacity',
            'remaining_capacity',
            'status',
            'skills',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'creator',
            'remaining_capacity',
            'created_at',
            'updated_at',
        ]

    def get_remaining_capacity(self, obj):
        return max(obj.capacity - obj.members.count(), 0)


class MyProjectsSerializer(ProjectSerializer):
    role = serializers.SerializerMethodField()

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['role']

    def get_role(self, obj):
        user = self.context['request'].user
        if obj.creator_id == user.id:
            return 'creator'
        return 'member'
