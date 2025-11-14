from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    Now requires superuser for super admin panel.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff and request.user.is_superuser)


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows authenticated users to read,
    but only allows admin users to write (create, update, delete).
    """
    def has_permission(self, request, view):
        # Check if user is authenticated first
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow read access for authenticated users (sellers can read filter options)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Require admin (superuser) for write operations
        return bool(request.user.is_staff and request.user.is_superuser)