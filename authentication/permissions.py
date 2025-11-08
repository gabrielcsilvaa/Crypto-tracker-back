from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

class IsSelfOrAdmin(BasePermission):
    """
    Para detail de usuário: libera se for o próprio user (id) ou admin.
    """
    def has_object_permission(self, request, view, obj):
        return bool(request.user and (request.user.is_staff or obj == request.user))

    def has_permission(self, request, view):
        # Permite acessar; a checagem fina é feita em has_object_permission
        return bool(request.user and request.user.is_authenticated)
