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
