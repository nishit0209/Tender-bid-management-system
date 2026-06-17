"""
Tender Model — Tenders App
Enterprise Tender & Bid Management System
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from apps.accounts.models import TimeStampedModel
import datetime


# ─────────────────────────────────────────────
# Choices
# ─────────────────────────────────────────────
class TenderStatus(models.TextChoices):
    DRAFT             = 'draft',             _('Draft')
    PENDING_APPROVAL  = 'pending_approval',  _('Pending Manager Approval')
    OPEN              = 'open',              _('Open for Bidding')
    CLOSED            = 'closed',            _('Closed')
    UNDER_EVALUATION  = 'under_evaluation',  _('Under Evaluation')
    AWARDED           = 'awarded',           _('Awarded')
    CANCELLED         = 'cancelled',         _('Cancelled')


class TenderCategory(models.TextChoices):
    GOODS            = 'goods',            _('Goods / Products')
    SERVICES         = 'services',         _('Services')
    WORKS            = 'works',            _('Works / Construction')
    CONSULTING       = 'consulting',       _('Consulting')
    IT               = 'it',               _('Information Technology')
    MAINTENANCE      = 'maintenance',      _('Maintenance & Repair')
    PRINTING         = 'printing',         _('Printing & Stationery')
    TRANSPORT        = 'transport',        _('Transport & Logistics')
    INFRASTRUCTURE   = 'infrastructure',   _('Infrastructure')
    OTHER            = 'other',            _('Other')


class TenderType(models.TextChoices):
    OPEN             = 'open',             _('Open Tender')
    LIMITED          = 'limited',          _('Limited Tender')
    SINGLE_SOURCE    = 'single_source',    _('Single Source')
    RATE_CONTRACT    = 'rate_contract',    _('Rate Contract')
    EOI              = 'eoi',              _('Expression of Interest')


# ─────────────────────────────────────────────
# Custom Manager
# ─────────────────────────────────────────────
class TenderManager(models.Manager):

    def draft(self):
        return self.filter(status=TenderStatus.DRAFT)

    def pending_approval(self):
        return self.filter(status=TenderStatus.PENDING_APPROVAL)

    def open(self):
        return self.filter(status=TenderStatus.OPEN)

    def active(self):
        """Open tenders that haven't closed yet."""
        return self.filter(status=TenderStatus.OPEN, closing_date__gt=timezone.now())

    def closed(self):
        return self.filter(status=TenderStatus.CLOSED)

    def awarded(self):
        return self.filter(status=TenderStatus.AWARDED)

    def by_category(self, category):
        return self.filter(category=category)


# ─────────────────────────────────────────────
# Auto-generate Tender Number
# ─────────────────────────────────────────────
def generate_tender_number():
    """Generate sequential tender number: TND-YYYY-XXXX"""
    year = datetime.datetime.now().year
    prefix = f'TND-{year}-'
    last = Tender.objects.filter(tender_number__startswith=prefix).order_by('-tender_number').first()
    if last:
        try:
            last_seq = int(last.tender_number.split('-')[-1])
        except (ValueError, IndexError):
            last_seq = 0
    else:
        last_seq = 0
    return f'{prefix}{str(last_seq + 1).zfill(4)}'


# ─────────────────────────────────────────────
# Tender Model
# ─────────────────────────────────────────────
class Tender(TimeStampedModel):
    """
    Represents a procurement tender/notice published by the organization.
    Follows: Draft → Pending Approval → Open → Closed → Under Evaluation → Awarded.
    """

    tender_number     = models.CharField(
                            max_length=20,
                            unique=True,
                            editable=False,
                            db_index=True,
                        )
    title             = models.CharField(max_length=255, db_index=True)
    description       = models.TextField()
    category          = models.CharField(
                            max_length=30,
                            choices=TenderCategory.choices,
                            default=TenderCategory.GOODS,
                            db_index=True,
                        )
    custom_category   = models.CharField(
                            max_length=100,
                            blank=True,
                            null=True,
                            help_text="Specify if category is 'Other'"
                        )
    tender_type       = models.CharField(
                            max_length=20,
                            choices=TenderType.choices,
                            default=TenderType.OPEN,
                        )

    # Specification
    quantity          = models.DecimalField(max_digits=12, decimal_places=2,
                                            null=True, blank=True)
    unit              = models.CharField(max_length=50, blank=True, null=True,
                                         help_text='Unit of measurement (kg, pcs, nos, etc.)')
    specifications    = models.TextField(blank=True, null=True,
                                         help_text='Detailed technical specifications')

    # Financial
    estimated_budget  = models.DecimalField(max_digits=15, decimal_places=2,
                                             verbose_name=_('Estimated Budget (INR)'))
    emd_amount        = models.DecimalField(max_digits=12, decimal_places=2,
                                            null=True, blank=True,
                                            verbose_name=_('Earnest Money Deposit (INR)'))

    # Dates
    publish_date      = models.DateTimeField(null=True, blank=True)
    opening_date      = models.DateTimeField(help_text='Date when bid submission opens')
    closing_date      = models.DateTimeField(help_text='Last date for bid submission', db_index=True)
    evaluation_date   = models.DateTimeField(null=True, blank=True,
                                             help_text='Expected date of evaluation')
    delivery_deadline = models.DateField(null=True, blank=True,
                                         help_text='Required delivery by date')

    # Terms
    terms_and_conditions = models.TextField(blank=True, null=True)
    eligibility_criteria = models.TextField(blank=True, null=True,
                                            help_text='Minimum eligibility criteria for vendors')
    is_pre_bid_meeting_required = models.BooleanField(default=False)
    pre_bid_meeting_date = models.DateTimeField(null=True, blank=True)
    pre_bid_meeting_location = models.CharField(max_length=255, blank=True, null=True)

    # Attachments
    tender_document   = models.FileField(
                            upload_to='tenders/documents/',
                            null=True, blank=True,
                            help_text='Official tender notice PDF',
                        )

    # Status & Workflow
    status            = models.CharField(
                            max_length=20,
                            choices=TenderStatus.choices,
                            default=TenderStatus.DRAFT,
                            db_index=True,
                        )
    cancellation_reason = models.TextField(blank=True, null=True)

    # Workflow Tracking
    created_by        = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.PROTECT,
                            related_name='tenders_created',
                        )
    submitted_for_approval_at = models.DateTimeField(null=True, blank=True)
    approved_by       = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='tenders_approved',
                        )
    approved_at       = models.DateTimeField(null=True, blank=True)
    approval_remarks  = models.TextField(blank=True, null=True)

    # Visibility
    is_public         = models.BooleanField(default=True)
    view_count        = models.PositiveIntegerField(default=0)

    objects = TenderManager()

    class Meta:
        verbose_name        = _('Tender')
        verbose_name_plural = _('Tenders')
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'closing_date']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['tender_number']),
        ]

    def __str__(self):
        return f"{self.tender_number} — {self.title} [{self.get_status_display()}]"

    # ── Status Properties ──────────────────────
    @property
    def is_open(self):
        return self.status == TenderStatus.OPEN

    @property
    def is_active(self):
        """Open and within submission window."""
        return (
            self.status == TenderStatus.OPEN
            and self.opening_date <= timezone.now() <= self.closing_date
        )

    @property
    def is_expired(self):
        return self.closing_date < timezone.now() if self.closing_date else False

    @property
    def days_remaining(self):
        if self.closing_date and self.status == TenderStatus.OPEN:
            delta = self.closing_date - timezone.now()
            return max(0, delta.days)
        return 0

    @property
    def bids_count(self):
        return self.bids.count()

    @property
    def can_accept_bids(self):
        return self.is_active

    @property
    def is_draft(self):
        return self.status == TenderStatus.DRAFT

    # ── Business Logic ─────────────────────────
    def submit_for_approval(self, user):
        """Procurement officer submits tender for manager approval."""
        self.status = TenderStatus.PENDING_APPROVAL
        self.submitted_for_approval_at = timezone.now()
        self.save(update_fields=['status', 'submitted_for_approval_at', 'updated_at'])

    def approve(self, manager, remarks=''):
        """Manager approves and publishes the tender."""
        self.status = TenderStatus.OPEN
        self.approved_by = manager
        self.approved_at = timezone.now()
        self.publish_date = timezone.now()
        self.approval_remarks = remarks
        self.save(update_fields=[
            'status', 'approved_by', 'approved_at',
            'publish_date', 'approval_remarks', 'updated_at'
        ])

    def reject(self, manager, remarks):
        """Manager rejects the tender — returns to draft."""
        self.status = TenderStatus.DRAFT
        self.approved_by = manager
        self.approved_at = timezone.now()
        self.approval_remarks = remarks
        self.save(update_fields=[
            'status', 'approved_by', 'approved_at', 'approval_remarks', 'updated_at'
        ])

    def close(self):
        """Close tender for bid submission."""
        self.status = TenderStatus.CLOSED
        self.save(update_fields=['status', 'updated_at'])

    def cancel(self, reason):
        """Cancel the tender."""
        self.status = TenderStatus.CANCELLED
        self.cancellation_reason = reason
        self.save(update_fields=['status', 'cancellation_reason', 'updated_at'])

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tenders:detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.tender_number:
            self.tender_number = generate_tender_number()
        super().save(*args, **kwargs)
