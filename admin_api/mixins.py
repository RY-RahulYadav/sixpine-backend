"""
Mixins for admin viewsets
"""
from .utils import create_admin_log


class AdminLoggingMixin:
    """Mixin to add automatic logging to admin viewsets"""
    
    def perform_create(self, serializer):
        """Log creation"""
        instance = serializer.save()
        try:
            create_admin_log(
                request=self.request,
                action_type='create',
                model_name=self.get_model_name(),
                object_id=instance.id,
                object_repr=str(instance),
                details=self.get_log_details(instance, 'create')
            )
        except Exception as e:
            print(f"Error creating admin log: {e}")
    
    def perform_update(self, serializer):
        """Log update"""
        instance = serializer.save()
        try:
            create_admin_log(
                request=self.request,
                action_type='update',
                model_name=self.get_model_name(),
                object_id=instance.id,
                object_repr=str(instance),
                details=self.get_log_details(instance, 'update')
            )
        except Exception as e:
            print(f"Error creating admin log: {e}")
    
    def perform_destroy(self, instance):
        """Log deletion"""
        try:
            create_admin_log(
                request=self.request,
                action_type='delete',
                model_name=self.get_model_name(),
                object_id=instance.id,
                object_repr=str(instance),
                details=self.get_log_details(instance, 'delete')
            )
        except Exception as e:
            print(f"Error creating admin log: {e}")
        instance.delete()
    
    def get_model_name(self):
        """Get model name for logging"""
        if hasattr(self, 'queryset') and self.queryset.model:
            return self.queryset.model.__name__
        return 'Unknown'
    
    def get_log_details(self, instance, action):
        """Get additional details for logging"""
        return {
            'action': action,
            'model': self.get_model_name()
        }

