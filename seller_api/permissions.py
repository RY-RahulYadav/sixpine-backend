from rest_framework import permissions


class IsVendorUser(permissions.BasePermission):
    """
    Permission check for vendor/seller users.
    User must have a vendor profile and it must be active.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has vendor profile
        if not hasattr(request.user, 'vendor_profile'):
            return False
        
        vendor = request.user.vendor_profile
        return vendor.is_active


class IsVendorOwner(permissions.BasePermission):
    """
    Permission check to ensure vendor can only access their own resources.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'vendor_profile'):
            return False
        
        vendor = request.user.vendor_profile
        
        # Check if object has vendor field and it matches
        if hasattr(obj, 'vendor'):
            return obj.vendor == vendor
        
        # For order items, check via product
        if hasattr(obj, 'product') and hasattr(obj.product, 'vendor'):
            return obj.product.vendor == vendor
        
        return False

