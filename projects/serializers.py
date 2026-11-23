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
    required=True,
    allow_empty=False
    )

    custom_skills = serializers.ListField(
    child=serializers.CharField(max_length=100),
    required=False,
    write_only=True,
    allow_empty=True
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

    def validate_custom_skills(self, value):
        cleaned_skills = []
        seen = set()

        for skill_name in value:
            skill_name = skill_name.strip()

            if not skill_name:
                raise serializers.ValidationError(
                    "Skill names cannot be empty."
                )

            normalized_name = skill_name.casefold()

            if normalized_name not in seen:
                cleaned_skills.append(skill_name)
                seen.add(normalized_name)

        return cleaned_skills
    
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

    def validate_skills(self, value):
        if len(value) > 10:
            raise serializers.ValidationError(
                "You can select a maximum of 10 skills."
            )
        return value

class MyProjectsSerializer(ProjectSerializer):
    role = serializers.SerializerMethodField()

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['role']

    def get_role(self, obj):
        user = self.context['request'].user

        if obj.creator_id == user.id:
            return 'creator'

        return 'member'
