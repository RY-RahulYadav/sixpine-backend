from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import User, OTPVerification, PasswordResetToken, ContactQuery, BulkOrder


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_verified', 'is_active', 'whatsapp_enabled', 'email_promotional', 'date_joined')
    list_filter = ('is_verified', 'is_active', 'is_staff', 'is_superuser', 'whatsapp_enabled', 'email_promotional', 'advertising_enabled', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'mobile')
    ordering = ('-date_joined',)
    actions = ['delete_selected_users', 'activate_users', 'deactivate_users']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'mobile')}),
        ('User Preferences', {
            'fields': ('interests', 'advertising_enabled'),
            'classes': ('collapse',)
        }),
        ('Communication Preferences', {
            'fields': ('whatsapp_enabled', 'whatsapp_order_updates', 'whatsapp_promotional', 'email_promotional'),
            'classes': ('collapse',)
        }),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('user_preferences_display',)
    
    def user_preferences_display(self, obj):
        """Display user preferences in a formatted way"""
        if not obj.pk:
            return "Save user first to see preferences"
        
        html = '<div style="padding: 10px; background: #f9f9f9; border-radius: 5px;">'
        
        # Interest Preferences
        html += '<h3 style="margin-top: 0;">Interest Preferences</h3>'
        interests = obj.interests or []
        if isinstance(interests, str):
            import json
            try:
                interests = json.loads(interests)
            except:
                interests = []
        if interests:
            html += '<p><strong>Selected Interests:</strong> ' + ', '.join(interests) + '</p>'
        else:
            html += '<p><strong>Selected Interests:</strong> <em>None</em></p>'
        
        # Advertising Preferences
        html += '<h3>Advertising Preferences</h3>'
        html += f'<p><strong>Personalized Ads Enabled:</strong> {"Yes" if obj.advertising_enabled else "No"}</p>'
        
        # Communication Preferences
        html += '<h3>Communication Preferences</h3>'
        html += '<div style="margin-left: 20px;">'
        html += '<h4>WhatsApp</h4>'
        html += f'<p><strong>WhatsApp Enabled:</strong> {"Yes" if obj.whatsapp_enabled else "No"}</p>'
        html += f'<p><strong>Order Updates:</strong> {"Yes" if obj.whatsapp_order_updates else "No"}</p>'
        html += f'<p><strong>Promotional Messages:</strong> {"Yes" if obj.whatsapp_promotional else "No"}</p>'
        html += '<h4>Email</h4>'
        html += f'<p><strong>Promotional Emails:</strong> {"Yes" if obj.email_promotional else "No"}</p>'
        html += '</div>'
        
        html += '</div>'
        return mark_safe(html)
    user_preferences_display.short_description = 'User Preferences Summary'
    
    def get_fieldsets(self, request, obj=None):
        """Add preferences display to fieldsets"""
        fieldsets = list(super().get_fieldsets(request, obj))
        if obj:  # Only show for existing users
            # Insert preferences display after Personal info
            fieldsets.insert(2, ('User Preferences Summary', {
                'fields': ('user_preferences_display',),
                'classes': ('collapse',)
            }))
        return fieldsets
    
    def delete_model(self, request, obj):
        """Custom delete to prevent deleting superusers"""
        if obj.is_superuser:
            messages.error(request, f'Cannot delete superuser: {obj.email}')
            return
        try:
            obj.delete()
            messages.success(request, f'User {obj.email} has been deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
    
    def delete_selected_users(self, request, queryset):
        """Custom bulk delete action"""
        deleted_count = 0
        for user in queryset:
            if user.is_superuser:
                messages.warning(request, f'Cannot delete superuser: {user.email}')
                continue
            try:
                user.delete()
                deleted_count += 1
            except Exception as e:
                messages.error(request, f'Error deleting {user.email}: {str(e)}')
        
        if deleted_count > 0:
            messages.success(request, f'Successfully deleted {deleted_count} user(s).')
        return HttpResponseRedirect(request.get_full_path())
    delete_selected_users.short_description = 'Delete selected users'
    
    def activate_users(self, request, queryset):
        """Bulk activate users"""
        updated = queryset.update(is_active=True)
        messages.success(request, f'Successfully activated {updated} user(s).')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        """Bulk deactivate users"""
        # Prevent deactivating superusers
        superusers = queryset.filter(is_superuser=True)
        if superusers.exists():
            messages.warning(request, f'Cannot deactivate {superusers.count()} superuser(s).')
        
        updated = queryset.exclude(is_superuser=True).update(is_active=False)
        if updated > 0:
            messages.success(request, f'Successfully deactivated {updated} user(s).')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting superusers"""
        if obj and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """OTP Verification admin"""
    list_display = ('email', 'mobile', 'otp_method', 'is_verified', 'is_used', 'created_at', 'expires_at')
    list_filter = ('otp_method', 'is_verified', 'is_used', 'created_at')
    search_fields = ('email', 'mobile', 'otp_code')
    readonly_fields = ('otp_code', 'created_at', 'expires_at')
    ordering = ('-created_at',)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Password Reset Token admin"""
    list_display = ('user', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'user__username', 'token')
    readonly_fields = ('token', 'created_at', 'expires_at')
    ordering = ('-created_at',)


@admin.register(ContactQuery)
class ContactQueryAdmin(admin.ModelAdmin):
    """Contact Query admin"""
    list_display = ('full_name', 'phone_number', 'email', 'pincode', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('full_name', 'phone_number', 'email', 'pincode')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    ordering = ('-created_at',)
    list_editable = ('status',)


@admin.register(BulkOrder)
class BulkOrderAdmin(admin.ModelAdmin):
    """Bulk Order admin"""
    list_display = ('company_name', 'contact_person', 'email', 'project_type', 'status', 'created_at')
    list_filter = ('status', 'project_type', 'created_at')
    search_fields = ('company_name', 'contact_person', 'email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_editable = ('status',)
