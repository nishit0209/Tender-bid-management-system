"""
Admin Registration — Evaluations App
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Evaluation


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = [
        'bid', 'price_score', 'experience_score', 'warranty_score',
        'delivery_score', 'total_score_display', 'grade_display',
        'rank', 'is_winner', 'status_badge', 'evaluated_by',
    ]
    list_filter = ['status', 'is_winner', 'created_at']
    search_fields = [
        'bid__tender__tender_number', 'bid__vendor__company_name',
    ]
    ordering = ['-total_score']
    readonly_fields = [
        'total_score', 'created_at', 'updated_at',
        'evaluated_at', 'approved_at', 'rank',
    ]

    fieldsets = (
        ('Bid Reference', {'fields': ('bid',)}),
        ('Scoring', {
            'fields': (
                'price_score', 'price_remarks',
                'experience_score', 'experience_remarks',
                'warranty_score', 'warranty_remarks',
                'delivery_score', 'delivery_remarks',
                'total_score',
            ),
        }),
        ('Evaluation Summary', {
            'fields': (
                'recommendation', 'overall_remarks', 'rank', 'is_winner',
            ),
        }),
        ('Workflow', {
            'fields': (
                'status', 'evaluated_by', 'evaluated_at',
                'approved_by', 'approved_at', 'approval_remarks',
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def total_score_display(self, obj):
        color = '#10B981' if float(obj.total_score) >= 70 else '#F59E0B' if float(obj.total_score) >= 50 else '#EF4444'
        return format_html(
            '<strong style="color:{};">{}/100</strong>',
            color, obj.total_score
        )
    total_score_display.short_description = 'Total Score'

    def grade_display(self, obj):
        return format_html('<strong>{}</strong>', obj.grade)
    grade_display.short_description = 'Grade'

    def status_badge(self, obj):
        colors = {
            'draft':            '#6B7280',
            'completed':        '#3B82F6',
            'pending_approval': '#F59E0B',
            'approved':         '#10B981',
            'rejected':         '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
