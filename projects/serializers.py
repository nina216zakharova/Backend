from rest_framework import serializers
from .models import Project, Skill, ProjectMember


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']
        

class ProjectSerializer(serializers.ModelSerializer):
    skills = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.all(),
        required=False
    )

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'goal',
            'description',
            'creator',
            'capacity',
            'status',
            'skills',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'creator',
            'created_at',
            'updated_at',
        ]        


class MyProjectsSerializer(ProjectSerializer):
    role = serializers.SerializerMethodField()

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['role']

    def get_role(self, obj):
        user = self.context['request'].user

        if obj.creator_id == user.id:
            return 'creator'

        return 'member'
