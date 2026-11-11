from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCreatorOrReadOnly(BasePermission):
    """
    Allow anyone to view a project.
    Only the project creator can update or delete it.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read-only methods for everyone
        if request.method in SAFE_METHODS:
            return True

        # Only the project creator can modify or delete it
        return obj.creator_id == request.user.id
