from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
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


class MembershipStatsView(APIView):
    """
    Aggregated membership request metrics for user dashboard.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        sent = MembershipRequest.objects.filter(user=user)
        received = MembershipRequest.objects.filter(project__creator=user)

        by_project = (
            received.filter(status=MembershipRequest.STATUS_PENDING)
            .values('project_id', 'project__title')
            .annotate(pending_count=models.Count('id'))
            .order_by('-pending_count')
        )

        data = {
            "sent": {
                "total": sent.count(),
                "pending": sent.filter(status=MembershipRequest.STATUS_PENDING).count(),
                "accepted": sent.filter(status=MembershipRequest.STATUS_ACCEPTED).count(),
                "rejected": sent.filter(status=MembershipRequest.STATUS_REJECTED).count(),
            },
            "received": {
                "total": received.count(),
                "pending": received.filter(status=MembershipRequest.STATUS_PENDING).count(),
                "accepted": received.filter(status=MembershipRequest.STATUS_ACCEPTED).count(),
                "rejected": received.filter(status=MembershipRequest.STATUS_REJECTED).count(),
            },
            "projects_to_review": [
                {
                    "project_id": item['project_id'],
                    "project_title": item['project__title'],
                    "pending_count": item['pending_count'],
                }
                for item in by_project
            ],
        }
        return Response(data, status=status.HTTP_200_OK)
