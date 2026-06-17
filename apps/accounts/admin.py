"""
Admin Registration — Accounts App
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, SystemLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin for CustomUser with role management."""

    list_display = [
        'email', 'get_full_name', 'role', 'is_active',
        'is_verified', 'is_staff', 'created_at',
    ]
    list_filter = ['role', 'is_active', 'is_verified', 'is_staff', 'created_at']
    search_fields = ['email', 'first_name', 'last_name', 'phone', 'employee_id']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'password_reset_token']

    fieldsets = (
        (_('Login Credentials'), {
            'fields': ('email', 'username', 'password'),
        }),
        (_('Personal Information'), {
            'fields': (
                'first_name', 'last_name', 'phone', 'profile_picture',
            ),
        }),
        (_('Role & Organization'), {
            'fields': (
                'role', 'department', 'designation', 'employee_id',
            ),
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_verified', 'is_staff', 'is_superuser',
                'groups', 'user_permissions',
            ),
            'classes': ('collapse',),
        }),
        (_('Security'), {
            'fields': (
                'email_verified', 'last_login_ip', 'failed_login_attempts',
                'account_locked_until', 'password_reset_token',
            ),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'role',
                'password1', 'password2',
            ),
        }),
    )

    def get_full_name(self, obj):
        return obj.get_full_name() or '—'
    get_full_name.short_description = 'Full Name'


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'get_user_display', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__email', 'email', 'ip_address']
    readonly_fields = ['user', 'email', 'action', 'ip_address', 'user_agent', 'created_at']

    def get_user_display(self, obj):
        return obj.user.email if obj.user else obj.email
    get_user_display.short_description = 'User'

    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
