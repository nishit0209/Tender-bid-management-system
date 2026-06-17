"""
Admin Registration — Vendors App
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Vendor, VendorDocument


class VendorDocumentInline(admin.TabularInline):
    model = VendorDocument
    extra = 0
    readonly_fields = ['created_at', 'verified_at', 'file_size']
    fields = [
        'document_type', 'file', 'status',
        'verified_by', 'verified_at', 'rejection_reason',
    ]


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        'company_name', 'gst_number', 'contact_person',
        'status_badge', 'completion_badge', 'verified_by',
        'approved_by', 'created_at',
    ]
    list_filter = ['status', 'business_type', 'state', 'created_at']
    search_fields = [
        'company_name', 'gst_number', 'pan_number', 'cin_number',
        'contact_person', 'contact_email', 'contact_phone',
    ]
    ordering = ['-created_at']
    raw_id_fields = ['user', 'verified_by', 'approved_by']
    readonly_fields = [
        'created_at', 'updated_at', 'submitted_at',
        'verified_at', 'approved_at', 'completion_percentage',
    ]
    inlines = [VendorDocumentInline]

    fieldsets = (
        (_('Company Information'), {
            'fields': (
                'user', 'company_name', 'gst_number', 'pan_number',
                'cin_number', 'msme_number', 'business_type',
                'year_established', 'annual_turnover', 'employee_count',
                'category_of_goods', 'website',
            ),
        }),
        (_('Contact Details'), {
            'fields': (
                'contact_person', 'contact_email', 'contact_phone', 'alternate_phone',
            ),
        }),
        (_('Address'), {
            'fields': (
                'address_line1', 'address_line2', 'city', 'state', 'pincode', 'country',
            ),
        }),
        (_('Bank Details'), {
            'fields': (
                'bank_name', 'bank_account_number', 'bank_ifsc', 'bank_branch',
            ),
            'classes': ('collapse',),
        }),
        (_('Status & Workflow'), {
            'fields': (
                'status', 'rejection_reason', 'suspension_reason',
                'verified_by', 'verified_at', 'approved_by', 'approved_at',
            ),
        }),
        (_('Internal'), {
            'fields': ('internal_notes', 'completion_percentage', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending':   '#F59E0B',
            'verified':  '#3B82F6',
            'approved':  '#10B981',
            'rejected':  '#EF4444',
            'suspended': '#6B7280',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def completion_badge(self, obj):
        pct = obj.completion_percentage
        color = '#10B981' if pct >= 80 else '#F59E0B' if pct >= 50 else '#EF4444'
        return format_html(
            '<span style="color:{};">{}</span>',
            color, f'{pct}%'
        )
    completion_badge.short_description = 'Profile %'


@admin.register(VendorDocument)
class VendorDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'vendor', 'document_type', 'status',
        'verified_by', 'verified_at', 'created_at',
    ]
    list_filter = ['status', 'document_type', 'created_at']
    search_fields = ['vendor__company_name', 'document_name']
    readonly_fields = ['created_at', 'updated_at', 'verified_at', 'file_size']
    ordering = ['-created_at']
