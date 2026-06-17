"""
Admin Registration — Purchase Orders App
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import PurchaseOrder


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'po_number', 'tender', 'vendor', 'total_amount',
        'delivery_date', 'status_badge', 'is_overdue_flag',
        'generated_by', 'approved_by', 'created_at',
    ]
    list_filter = ['status', 'created_at', 'delivery_date']
    search_fields = [
        'po_number', 'tender__tender_number',
        'vendor__company_name', 'vendor__gst_number',
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'po_number', 'total_amount', 'created_at', 'updated_at',
        'approved_at', 'dispatched_at', 'delivered_at',
    ]
    date_hierarchy = 'delivery_date'

    fieldsets = (
        ('PO Reference', {
            'fields': ('po_number', 'tender', 'vendor', 'evaluation'),
        }),
        ('Financial Details', {
            'fields': ('amount', 'tax_amount', 'total_amount', 'payment_terms'),
        }),
        ('Delivery', {
            'fields': (
                'delivery_date', 'delivery_address', 'delivery_instructions',
            ),
        }),
        ('Terms', {
            'fields': ('terms_and_conditions', 'penalty_clause'),
        }),
        ('Line Items', {
            'fields': ('line_items',),
            'classes': ('collapse',),
        }),
        ('Status & Workflow', {
            'fields': (
                'status', 'generated_by', 'approved_by', 'approved_at',
                'approval_remarks', 'cancellation_reason',
            ),
        }),
        ('Delivery Tracking', {
            'fields': (
                'dispatched_at', 'delivered_at', 'delivery_proof',
            ),
            'classes': ('collapse',),
        }),
        ('Notes & Timestamps', {
            'fields': ('internal_notes', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        colors = {
            'draft':       '#6B7280',
            'pending':     '#F59E0B',
            'approved':    '#3B82F6',
            'in_progress': '#8B5CF6',
            'delivered':   '#059669',
            'completed':   '#10B981',
            'cancelled':   '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def is_overdue_flag(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color:#EF4444;font-weight:bold;">⚠ OVERDUE</span>')
        return format_html('<span style="color:#10B981;">✓ On Track</span>')
    is_overdue_flag.short_description = 'Delivery'
