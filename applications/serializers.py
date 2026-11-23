from rest_framework import serializers
from django.db import transaction
from .models import MembershipRequest
from projects.models import Project, ProjectMember


class MembershipRequestSerializer(serializers.ModelSerializer):
    applicant_username = serializers.ReadOnlyField(source='user.username')
    applicant_email = serializers.ReadOnlyField(source='user.email')
    project_title = serializers.ReadOnlyField(source='project.title')

    class Meta:
        model = MembershipRequest
        fields = [
            'id',
            'project',
            'project_title',
            'user',
            'applicant_username',
            'applicant_email',
            'status',
            'message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'project',
            'project_title',
            'user',
            'applicant_username',
            'applicant_email',
            'status',
            'created_at',
            'updated_at',
        ]


class MembershipRequestCreateSerializer(serializers.ModelSerializer):
    applicant_username = serializers.ReadOnlyField(source='user.username')
    status = serializers.ReadOnlyField()
    created_at = serializers.ReadOnlyField()

    class Meta:
        model = MembershipRequest
        fields = ['id', 'project', 'message', 'status', 'applicant_username', 'created_at']
        read_only_fields = ['id', 'status', 'applicant_username', 'created_at']

    def validate_project(self, project):
        user = self.context['request'].user

        if project.status != Project.STATUS_OPEN:
            raise serializers.ValidationError("Cannot apply to a closed project.")

        if project.creator == user:
            raise serializers.ValidationError("You cannot apply to your own project.")

        if ProjectMember.objects.filter(project=project, user=user).exists():
            raise serializers.ValidationError("You are already a member of this project.")

        if MembershipRequest.objects.filter(
            project=project,
            user=user,
            status=MembershipRequest.STATUS_PENDING,
        ).exists():
            raise serializers.ValidationError("You already have a pending request for this project.")

        if project.members.count() >= project.capacity:
            raise serializers.ValidationError("Project team capacity is already full.")

        return project

    def create(self, validated_data):
        user = self.context['request'].user
        return MembershipRequest.objects.create(user=user, **validated_data)


class MembershipRequestStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipRequest
        fields = ['status']

    def validate_status(self, value):
        valid_transitions = [MembershipRequest.STATUS_ACCEPTED, MembershipRequest.STATUS_REJECTED]
        if value not in valid_transitions:
            raise serializers.ValidationError("Status can only be updated to 'accepted' or 'rejected'.")
        return value

    def update(self, instance, validated_data):
        new_status = validated_data.get('status')
        request_user = self.context['request'].user

        if instance.project.creator != request_user:
            raise serializers.ValidationError(
                {"detail": "Only the project creator can accept or reject requests."}
            )

        if instance.status != MembershipRequest.STATUS_PENDING:
            raise serializers.ValidationError(
                {"detail": f"This request is already {instance.status}."}
            )

        with transaction.atomic():
            instance.status = new_status
            instance.save(update_fields=['status', 'updated_at'])

            if new_status == MembershipRequest.STATUS_ACCEPTED:
                project = Project.objects.select_for_update().get(pk=instance.project_id)

                if project.members.count() >= project.capacity:
                    raise serializers.ValidationError(
                        {"detail": "Cannot accept request because project capacity is full."}
                    )

                ProjectMember.objects.get_or_create(
                    project=project,
                    user=instance.user,
                )

                if project.members.count() >= project.capacity:
                    project.status = Project.STATUS_CLOSED
                    project.save(update_fields=['status', 'updated_at'])

        return instance
