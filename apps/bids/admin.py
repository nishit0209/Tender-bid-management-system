"""
Admin Registration — Bids App
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Bid


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'tender', 'vendor', 'bid_amount', 'total_bid_amount_display',
        'delivery_timeline_days', 'warranty_period_months',
        'status_badge', 'submitted_at',
    ]
    list_filter = ['status', 'submitted_at', 'tender__category']
    search_fields = [
        'tender__tender_number', 'tender__title',
        'vendor__company_name', 'vendor__gst_number',
    ]
    ordering = ['-submitted_at']
    readonly_fields = ['submitted_at', 'created_at', 'updated_at', 'reviewed_at']

    fieldsets = (
        ('Bid Reference', {
            'fields': ('tender', 'vendor'),
        }),
        ('Financial Details', {
            'fields': (
                'bid_amount', 'tax_percentage', 'discount_percentage',
            ),
        }),
        ('Delivery & Warranty', {
            'fields': ('delivery_timeline_days', 'warranty_period_months'),
        }),
        ('Documents', {
            'fields': ('technical_proposal', 'commercial_proposal'),
        }),
        ('Additional', {
            'fields': ('notes', 'is_compliant', 'emd_paid', 'emd_reference'),
        }),
        ('Status & Workflow', {
            'fields': (
                'status', 'reviewed_by', 'reviewed_at',
                'rejection_reason', 'internal_remarks',
            ),
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        colors = {
            'submitted':    '#3B82F6',
            'under_review': '#F59E0B',
            'shortlisted':  '#8B5CF6',
            'rejected':     '#EF4444',
            'approved':     '#10B981',
            'withdrawn':    '#6B7280',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def total_bid_amount_display(self, obj):
        return f'₹{obj.total_bid_amount:,.2f}'
    total_bid_amount_display.short_description = 'Total Bid Amt'
