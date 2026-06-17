"""
Admin Registration — Notifications App
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'recipient', 'notification_type', 'priority_badge',
        'is_read', 'email_sent', 'created_at',
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read', 'email_sent', 'created_at',
    ]
    search_fields = ['title', 'message', 'recipient__email', 'recipient__first_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'read_at', 'email_sent_at']

    fieldsets = (
        ('Recipient', {'fields': ('recipient',)}),
        ('Content', {
            'fields': ('notification_type', 'priority', 'title', 'message', 'action_url'),
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'email_sent', 'email_sent_at'),
        }),
        ('Related Objects', {
            'fields': (
                'related_tender', 'related_vendor',
                'related_bid', 'related_po',
            ),
            'classes': ('collapse',),
        }),
        ('Extra Data', {
            'fields': ('extra_data',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def priority_badge(self, obj):
        colors = {
            'low':    '#6B7280',
            'medium': '#3B82F6',
            'high':   '#F59E0B',
            'urgent': '#EF4444',
        }
        color = colors.get(obj.priority, '#6B7280')
        return format_html(
            '<span style="background:{};color:white;padding:2px 6px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'

    actions = ['mark_as_read', 'mark_as_unread']

    @admin.action(description='Mark selected as read')
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        self.message_user(request, f'{updated} notification(s) marked as read.')

    @admin.action(description='Mark selected as unread')
    def mark_as_unread(self, request, queryset):
        updated = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
