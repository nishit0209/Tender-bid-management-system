"""
Admin Registration — Tenders App
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Tender


@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = [
        'tender_number', 'title', 'category', 'status_badge',
        'estimated_budget', 'closing_date', 'bids_count',
        'created_by', 'created_at',
    ]
    list_filter = ['status', 'category', 'tender_type', 'created_at']
    search_fields = ['tender_number', 'title', 'description']
    ordering = ['-created_at']
    readonly_fields = [
        'tender_number', 'created_at', 'updated_at',
        'publish_date', 'submitted_for_approval_at', 'approved_at',
        'bids_count', 'view_count',
    ]
    date_hierarchy = 'closing_date'

    fieldsets = (
        ('Tender Details', {
            'fields': (
                'tender_number', 'title', 'description', 'category',
                'tender_type', 'specifications',
            ),
        }),
        ('Quantity & Budget', {
            'fields': (
                'quantity', 'unit', 'estimated_budget', 'emd_amount',
            ),
        }),
        ('Important Dates', {
            'fields': (
                'opening_date', 'closing_date',
                'evaluation_date', 'delivery_deadline',
            ),
        }),
        ('Pre-bid Meeting', {
            'fields': (
                'is_pre_bid_meeting_required',
                'pre_bid_meeting_date', 'pre_bid_meeting_location',
            ),
            'classes': ('collapse',),
        }),
        ('Terms & Eligibility', {
            'fields': (
                'terms_and_conditions', 'eligibility_criteria', 'tender_document',
            ),
            'classes': ('collapse',),
        }),
        ('Workflow', {
            'fields': (
                'status', 'created_by', 'submitted_for_approval_at',
                'approved_by', 'approved_at', 'approval_remarks',
                'cancellation_reason',
            ),
        }),
        ('Analytics', {
            'fields': ('is_public', 'view_count', 'bids_count', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        colors = {
            'draft':            '#6B7280',
            'pending_approval': '#F59E0B',
            'open':             '#10B981',
            'closed':           '#3B82F6',
            'under_evaluation': '#8B5CF6',
            'awarded':          '#059669',
            'cancelled':        '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def bids_count(self, obj):
        return obj.bids.count()
    bids_count.short_description = '# Bids'
