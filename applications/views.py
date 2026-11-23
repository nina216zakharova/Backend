from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import MembershipRequest
from .permissions import IsApplicantOrProjectCreator
from .serializers import (
    MembershipRequestSerializer,
    MembershipRequestCreateSerializer,
    MembershipRequestStatusUpdateSerializer,
)


class MembershipRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MembershipRequestCreateSerializer
        return MembershipRequestSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = MembershipRequest.objects.filter(
            models.Q(user=user) | models.Q(project__creator=user)
        ).select_related('project', 'user')

        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        req_status = self.request.query_params.get('status')
        if req_status:
            queryset = queryset.filter(status=req_status)

        role = self.request.query_params.get('role')
        if role == 'applicant':
            queryset = queryset.filter(user=user)
        elif role == 'creator':
            queryset = queryset.filter(project__creator=user)

        return queryset.order_by('-created_at')


class MembershipRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsApplicantOrProjectCreator]
    queryset = MembershipRequest.objects.all().select_related('project', 'user')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MembershipRequestStatusUpdateSerializer
        return MembershipRequestSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.user_id != request.user.id:
            raise PermissionDenied("Only the applicant can withdraw this request.")

        if instance.status != MembershipRequest.STATUS_PENDING:
            raise ValidationError(
                {"detail": "Only pending requests can be withdrawn."}
            )

        instance.delete()
        return Response(
            {"message": "Membership request withdrawn successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
