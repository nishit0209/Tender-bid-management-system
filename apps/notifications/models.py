"""
Notification Model — Notifications App
Enterprise Tender & Bid Management System
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.accounts.models import TimeStampedModel


# ─────────────────────────────────────────────
# Notification Type Choices
# ─────────────────────────────────────────────
class NotificationType(models.TextChoices):
    # Vendor Events
    VENDOR_REGISTERED       = 'vendor_registered',       _('Vendor Registered')
    VENDOR_VERIFIED         = 'vendor_verified',         _('Vendor Verified')
    VENDOR_APPROVED         = 'vendor_approved',         _('Vendor Approved')
    VENDOR_REJECTED         = 'vendor_rejected',         _('Vendor Rejected')
    VENDOR_SUSPENDED        = 'vendor_suspended',        _('Vendor Suspended')
    DOCUMENT_UPLOADED       = 'document_uploaded',       _('Document Uploaded')
    DOCUMENT_VERIFIED       = 'document_verified',       _('Document Verified')
    DOCUMENT_REJECTED       = 'document_rejected',       _('Document Rejected')

    # Tender Events
    TENDER_SUBMITTED        = 'tender_submitted',        _('Tender Submitted for Approval')
    TENDER_APPROVED         = 'tender_approved',         _('Tender Approved & Published')
    TENDER_REJECTED         = 'tender_rejected',         _('Tender Rejected')
    TENDER_PUBLISHED        = 'tender_published',        _('New Tender Published')
    TENDER_CLOSING_SOON     = 'tender_closing_soon',     _('Tender Closing Soon')
    TENDER_CLOSED           = 'tender_closed',           _('Tender Closed')
    TENDER_CANCELLED        = 'tender_cancelled',        _('Tender Cancelled')

    # Bid Events
    BID_SUBMITTED           = 'bid_submitted',           _('Bid Submitted')
    BID_UNDER_REVIEW        = 'bid_under_review',        _('Bid Under Review')
    BID_SHORTLISTED         = 'bid_shortlisted',         _('Bid Shortlisted')
    BID_APPROVED            = 'bid_approved',            _('Bid Approved — You are the Winner!')
    BID_REJECTED            = 'bid_rejected',            _('Bid Rejected')

    # Evaluation Events
    EVALUATION_SUBMITTED    = 'evaluation_submitted',   _('Evaluation Submitted for Approval')
    EVALUATION_APPROVED     = 'evaluation_approved',    _('Evaluation Approved')
    WINNER_SELECTED         = 'winner_selected',        _('Winner Selected')

    # Purchase Order Events
    PO_GENERATED            = 'po_generated',           _('Purchase Order Generated')
    PO_APPROVED             = 'po_approved',            _('Purchase Order Approved')
    PO_DISPATCHED           = 'po_dispatched',          _('Order Dispatched')
    PO_DELIVERED            = 'po_delivered',           _('Order Delivered')
    PO_COMPLETED            = 'po_completed',           _('Purchase Order Completed')

    # System Events
    SYSTEM_ALERT            = 'system_alert',           _('System Alert')
    ACCOUNT_VERIFIED        = 'account_verified',       _('Account Verified')
    PASSWORD_CHANGED        = 'password_changed',       _('Password Changed')


class NotificationPriority(models.TextChoices):
    LOW    = 'low',    _('Low')
    MEDIUM = 'medium', _('Medium')
    HIGH   = 'high',   _('High')
    URGENT = 'urgent', _('Urgent')


# ─────────────────────────────────────────────
# Custom Manager
# ─────────────────────────────────────────────
class NotificationManager(models.Manager):

    def for_user(self, user):
        return self.filter(recipient=user).order_by('-created_at')

    def unread_for_user(self, user):
        return self.filter(recipient=user, is_read=False).order_by('-created_at')

    def recent_for_user(self, user, limit=10):
        return self.filter(recipient=user).order_by('-created_at')[:limit]

    def mark_all_read(self, user):
        return self.filter(recipient=user, is_read=False).update(is_read=True)


# ─────────────────────────────────────────────
# Notification Model
# ─────────────────────────────────────────────
class Notification(TimeStampedModel):
    """
    In-app notification delivered to a specific user.
    Supports linking to related objects (tender, vendor, bid, PO).
    """

    recipient         = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE,
                            related_name='notifications',
                            db_index=True,
                        )

    notification_type = models.CharField(
                            max_length=50,
                            choices=NotificationType.choices,
                            db_index=True,
                        )
    priority          = models.CharField(
                            max_length=10,
                            choices=NotificationPriority.choices,
                            default=NotificationPriority.MEDIUM,
                        )

    # Content
    title             = models.CharField(max_length=255)
    message           = models.TextField()
    action_url        = models.CharField(max_length=500, blank=True, null=True,
                                         help_text='URL to navigate when notification is clicked')

    # Status
    is_read           = models.BooleanField(default=False, db_index=True)
    read_at           = models.DateTimeField(null=True, blank=True)

    # Email
    email_sent        = models.BooleanField(default=False)
    email_sent_at     = models.DateTimeField(null=True, blank=True)

    # Related Objects (nullable FK for context)
    related_tender    = models.ForeignKey(
                            'tenders.Tender',
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='notifications',
                        )
    related_vendor    = models.ForeignKey(
                            'vendors.Vendor',
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='notifications',
                        )
    related_bid       = models.ForeignKey(
                            'bids.Bid',
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='notifications',
                        )
    related_po        = models.ForeignKey(
                            'purchase_orders.PurchaseOrder',
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='notifications',
                        )

    # Metadata
    extra_data        = models.JSONField(default=dict, blank=True,
                                         help_text='Additional context data in JSON format')

    objects = NotificationManager()

    class Meta:
        verbose_name        = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', 'created_at']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title} → {self.recipient.full_name}"

    def mark_as_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])

    @property
    def icon_class(self):
        """Returns a CSS/icon class based on notification type."""
        icon_map = {
            'vendor_approved': 'check-circle',
            'vendor_rejected': 'x-circle',
            'tender_published': 'file-text',
            'bid_submitted': 'send',
            'bid_approved': 'award',
            'winner_selected': 'trophy',
            'po_generated': 'shopping-cart',
            'po_approved': 'check',
            'system_alert': 'alert-triangle',
        }
        return icon_map.get(self.notification_type, 'bell')

    @property
    def color_class(self):
        """Returns a Tailwind color class based on priority."""
        color_map = {
            'low':    'text-gray-500',
            'medium': 'text-blue-500',
            'high':   'text-orange-500',
            'urgent': 'text-red-500',
        }
        return color_map.get(self.priority, 'text-blue-500')


# ─────────────────────────────────────────────
# Notification Helper Function
# ─────────────────────────────────────────────
def create_notification(
    recipient,
    notification_type,
    title,
    message,
    priority=NotificationPriority.MEDIUM,
    action_url=None,
    related_tender=None,
    related_vendor=None,
    related_bid=None,
    related_po=None,
    extra_data=None,
):
    """
    Utility function to create a notification.
    Import this wherever you need to send notifications.
    """
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        priority=priority,
        title=title,
        message=message,
        action_url=action_url,
        related_tender=related_tender,
        related_vendor=related_vendor,
        related_bid=related_bid,
        related_po=related_po,
        extra_data=extra_data or {},
    )
