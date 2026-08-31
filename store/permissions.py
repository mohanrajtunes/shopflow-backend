from rest_framework import permissions

class IsVendorOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access for anyone, but write access 
    only to users whose role is 'vendor'.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.role == 'vendor'