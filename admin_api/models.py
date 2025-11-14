from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class GlobalSettings(models.Model):
    """Global settings for the admin panel"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Global Setting"
        verbose_name_plural = "Global Settings"
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value}"
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a setting value by key"""
        try:
            setting = cls.objects.get(key=key)
            # Try to convert to int if it's numeric
            try:
                return int(setting.value)
            except ValueError:
                return setting.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key, value, description=''):
        """Set a setting value by key"""
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={'value': str(value), 'description': description}
        )
        if not created:
            setting.value = str(value)
            if description:
                setting.description = description
            setting.save()
        return setting


class AdminLog(models.Model):
    """Admin action logs"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admin_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=255)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Admin Log"
        verbose_name_plural = "Admin Logs"
    
    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.model_name}"


class AdminDashboardSetting(models.Model):
    """User-specific dashboard settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_settings')
    layout_preference = models.CharField(max_length=50, default='default')
    widgets_order = models.JSONField(default=dict)
    theme_preference = models.CharField(max_length=50, default='light')
    show_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dashboard Settings for {self.user.username}"


class HomePageContent(models.Model):
    """Home page content sections for customization"""
    section_key = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique identifier for the section'
    )
    section_name = models.CharField(
        max_length=200,
        help_text='Human-readable section name'
    )
    content = models.JSONField(
        default=dict,
        help_text='Section content as JSON'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this section is visible on the home page'
    )
    order = models.IntegerField(
        default=0,
        help_text='Display order on the page'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Home Page Content"
        verbose_name_plural = "Home Page Contents"
        ordering = ['order', 'section_name']
    
    def __str__(self):
        return f"{self.section_name} ({self.section_key})"


class BulkOrderPageContent(models.Model):
    """Bulk order page content sections for customization"""
    section_key = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique identifier for the section'
    )
    section_name = models.CharField(
        max_length=200,
        help_text='Human-readable section name'
    )
    content = models.JSONField(
        default=dict,
        help_text='Section content as JSON'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this section is visible on the bulk order page'
    )
    order = models.IntegerField(
        default=0,
        help_text='Display order on the page'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bulk Order Page Content"
        verbose_name_plural = "Bulk Order Page Contents"
        ordering = ['order', 'section_name']
    
    def __str__(self):
        return f"{self.section_name} ({self.section_key})"