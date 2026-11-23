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
    accepted_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'goal',
            'description',
            'creator',
            'capacity',
            'accepted_count',
            'status',
            'project_type',
            'custom_project_type',
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
    def get_accepted_count(self, obj):
        return obj.members.count()
    
    def validate(self, attrs):
        project_type = attrs.get(
            'project_type',
            getattr(self.instance, 'project_type', '')
        )

        custom_project_type = attrs.get(
            'custom_project_type',
            getattr(self.instance, 'custom_project_type', '')
        )

        if project_type == 'other' and not custom_project_type.strip():
            raise serializers.ValidationError({
                'custom_project_type': 'Please specify your project type.'
            })

        return attrs

class MyProjectsSerializer(ProjectSerializer):
    role = serializers.SerializerMethodField()

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['role']

    def get_role(self, obj):
        user = self.context['request'].user

        if obj.creator_id == user.id:
            return 'creator'

        return 'member'
