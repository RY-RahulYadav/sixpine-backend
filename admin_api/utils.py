"""
Utility functions for admin operations
"""
from django.contrib.auth import get_user_model
from .models import AdminLog
from django.utils import timezone

User = get_user_model()


def create_admin_log(request, action_type, model_name, object_id=None, object_repr='', details=None):
    """
    Create an admin log entry
    
    Args:
        request: Django request object
        action_type: Type of action (create, update, delete, activate, deactivate, login, logout, view)
        model_name: Name of the model being acted upon
        object_id: ID of the object (optional)
        object_repr: String representation of the object (optional)
        details: Additional details as dict (optional)
    
    Returns:
        AdminLog instance
    """
    user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
    
    # Get IP address
    ip_address = None
    if hasattr(request, 'META'):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    # Get user agent
    user_agent = request.META.get('HTTP_USER_AGENT', '') if hasattr(request, 'META') else ''
    
    # Prepare details
    log_details = details or {}
    if not isinstance(log_details, dict):
        log_details = {'details': str(log_details)}
    
    # Create log entry
    log = AdminLog.objects.create(
        user=user,
        action_type=action_type,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr[:255] if object_repr else '',
        details=log_details,
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else ''
    )
    
    return log


def log_admin_action(action_type, model_name, user=None, object_id=None, object_repr='', details=None):
    """
    Create an admin log entry without request object (for background tasks)
    
    Args:
        action_type: Type of action
        model_name: Name of the model
        user: User instance (optional)
        object_id: ID of the object (optional)
        object_repr: String representation of the object (optional)
        details: Additional details as dict (optional)
    
    Returns:
        AdminLog instance
    """
    log_details = details or {}
    if not isinstance(log_details, dict):
        log_details = {'details': str(log_details)}
    
    log = AdminLog.objects.create(
        user=user,
        action_type=action_type,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr[:255] if object_repr else '',
        details=log_details,
        ip_address=None,
        user_agent=''
    )
    
    return log

