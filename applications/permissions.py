from rest_framework import permissions


class IsApplicantOrProjectCreator(permissions.BasePermission):
    """
    Applicant can view or cancel their own pending request.
    Project creator can view or update status (accept/reject).
    """

    def has_object_permission(self, request, view, obj):
        is_applicant = obj.user_id == request.user.id
        is_creator = obj.project.creator_id == request.user.id

        if request.method in permissions.SAFE_METHODS:
            return is_applicant or is_creator

        if request.method == 'DELETE':
            return is_applicant

        if request.method in ['PUT', 'PATCH']:
            return is_creator

        return False
