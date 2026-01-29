from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated

class IsRecruiter(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'recruiter'
        )

class IsManager(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'manager'
        )

class ReadOnly(BasePermission):

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
