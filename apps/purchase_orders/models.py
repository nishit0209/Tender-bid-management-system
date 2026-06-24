"""
PurchaseOrder Model — Purchase Orders App
Enterprise Tender & Bid Management System
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.accounts.models import TimeStampedModel
from apps.tenders.models import Tender
from apps.vendors.models import Vendor
from apps.evaluations.models import Evaluation
import datetime


# ─────────────────────────────────────────────
# Choices
# ─────────────────────────────────────────────
class POStatus(models.TextChoices):
    DRAFT       = 'draft',       _('Draft')
    PENDING     = 'pending',     _('Pending Approval')
    APPROVED    = 'approved',    _('Approved')
    IN_PROGRESS = 'in_progress', _('In Progress / Dispatched')
    DELIVERED   = 'delivered',   _('Delivered')
    COMPLETED   = 'completed',   _('Completed & Closed')
    CANCELLED   = 'cancelled',   _('Cancelled')


# ─────────────────────────────────────────────
# Auto-generate PO Number
# ─────────────────────────────────────────────
def generate_po_number():
    """Generate sequential PO number: PO-YYYY-XXXX"""
    year = datetime.datetime.now().year
    prefix = f'PO-{year}-'
    last = PurchaseOrder.objects.filter(po_number__startswith=prefix).order_by('-po_number').first()
    if last:
        try:
            last_seq = int(last.po_number.split('-')[-1])
        except (ValueError, IndexError):
            last_seq = 0
    else:
        last_seq = 0
    return f'{prefix}{str(last_seq + 1).zfill(4)}'


# ─────────────────────────────────────────────
# Custom Manager
# ─────────────────────────────────────────────
class PurchaseOrderManager(models.Manager):

    def pending(self):
        return self.filter(status=POStatus.PENDING)

    def approved(self):
        return self.filter(status=POStatus.APPROVED)

    def active(self):
        return self.filter(status__in=[POStatus.APPROVED, POStatus.IN_PROGRESS])

    def completed(self):
        return self.filter(status=POStatus.COMPLETED)

    def for_vendor(self, vendor):
        return self.filter(vendor=vendor)


# ─────────────────────────────────────────────
# PurchaseOrder Model
# ─────────────────────────────────────────────
class PurchaseOrder(TimeStampedModel):
    """
    Represents a Purchase Order generated after winner selection.
    Links Tender → Winning Vendor → Evaluation.
    """

    po_number         = models.CharField(
                            max_length=20,
                            unique=True,
                            editable=False,
                            db_index=True,
                        )

    # Core References
    tender            = models.ForeignKey(
                            Tender,
                            on_delete=models.PROTECT,
                            related_name='purchase_orders',
                        )
    vendor            = models.ForeignKey(
                            Vendor,
                            on_delete=models.PROTECT,
                            related_name='purchase_orders',
                        )
    evaluation        = models.OneToOneField(
                            Evaluation,
                            on_delete=models.PROTECT,
                            related_name='purchase_order',
                            null=True, blank=True,
                        )

    # Financial
    amount            = models.DecimalField(
                            max_digits=15, decimal_places=2,
                            verbose_name=_('PO Amount (INR)'),
                        )
    tax_amount        = models.DecimalField(
                            max_digits=12, decimal_places=2,
                            default=0,
                            verbose_name=_('Tax Amount (INR)'),
                        )
    total_amount      = models.DecimalField(
                            max_digits=15, decimal_places=2,
                            default=0,
                            verbose_name=_('Total Amount including Tax (INR)'),
                        )

    # Delivery
    delivery_date     = models.DateField(
                            verbose_name=_('Expected Delivery Date'),
                        )
    delivery_address  = models.TextField()
    delivery_instructions = models.TextField(blank=True, null=True)

    # Terms
    terms_and_conditions = models.TextField(
                               help_text='Standard terms and conditions for this PO',
                           )
    payment_terms     = models.CharField(max_length=255, blank=True, null=True,
                                         help_text='e.g. 30 days net, advance 20%, etc.')
    penalty_clause    = models.TextField(blank=True, null=True,
                                         help_text='Penalty for late delivery')

    # Items (JSON representation of ordered items)
    line_items        = models.JSONField(
                            default=list,
                            blank=True,
                            help_text='List of items: [{name, qty, unit, rate, amount}]',
                        )

    # Status & Workflow
    status            = models.CharField(
                            max_length=20,
                            choices=POStatus.choices,
                            default=POStatus.DRAFT,
                            db_index=True,
                        )
    cancellation_reason = models.TextField(blank=True, null=True)

    # Vendor Performance Rating
    vendor_rating     = models.PositiveSmallIntegerField(
                            null=True, blank=True,
                            help_text='Rating out of 5 for vendor performance'
                        )
    vendor_feedback   = models.TextField(
                            blank=True, null=True,
                            help_text='Internal feedback on vendor performance'
                        )

    # Delivery tracking
    dispatched_at     = models.DateTimeField(null=True, blank=True)
    delivered_at      = models.DateTimeField(null=True, blank=True)
    delivery_proof    = models.FileField(
                            upload_to='purchase_orders/delivery/',
                            null=True, blank=True,
                        )

    # Workflow Tracking
    generated_by      = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.PROTECT,
                            related_name='pos_generated',
                        )
    approved_by       = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='pos_approved',
                        )
    approved_at       = models.DateTimeField(null=True, blank=True)
    approval_remarks  = models.TextField(blank=True, null=True)

    # Notes
    internal_notes    = models.TextField(blank=True, null=True)

    objects = PurchaseOrderManager()

    class Meta:
        verbose_name        = _('Purchase Order')
        verbose_name_plural = _('Purchase Orders')
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['po_number']),
            models.Index(fields=['vendor', 'status']),
        ]

    def __str__(self):
        return f"{self.po_number} — {self.vendor.company_name} [{self.get_status_display()}]"

    @property
    def is_overdue(self):
        from django.utils import timezone
        return (
            self.delivery_date < timezone.now().date()
            and self.status not in [POStatus.DELIVERED, POStatus.COMPLETED, POStatus.CANCELLED]
        )

    @property
    def days_until_delivery(self):
        from django.utils import timezone
        delta = self.delivery_date - timezone.now().date()
        return delta.days

    def calculate_total(self):
        return round(float(self.amount) + float(self.tax_amount), 2)

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = generate_po_number()
        # Auto-compute total
        self.total_amount = self.calculate_total()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('purchase_orders:detail', kwargs={'pk': self.pk})
