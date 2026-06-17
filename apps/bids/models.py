"""
Bid Model — Bids App
Enterprise Tender & Bid Management System
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.accounts.models import TimeStampedModel
from apps.tenders.models import Tender
from apps.vendors.models import Vendor
import os


# ─────────────────────────────────────────────
# Choices
# ─────────────────────────────────────────────
class BidStatus(models.TextChoices):
    SUBMITTED     = 'submitted',      _('Submitted')
    UNDER_REVIEW  = 'under_review',   _('Under Review')
    SHORTLISTED   = 'shortlisted',    _('Shortlisted')
    REJECTED      = 'rejected',       _('Rejected')
    APPROVED      = 'approved',       _('Approved / Winner')
    WITHDRAWN     = 'withdrawn',      _('Withdrawn by Vendor')


# ─────────────────────────────────────────────
# Upload Paths
# ─────────────────────────────────────────────
def bid_technical_proposal_path(instance, filename):
    """bids/<tender_id>/<vendor_id>/technical/<filename>"""
    ext = os.path.splitext(filename)[1]
    return f'bids/{instance.tender.id}/{instance.vendor.id}/technical/proposal{ext}'


def bid_commercial_proposal_path(instance, filename):
    """bids/<tender_id>/<vendor_id>/commercial/<filename>"""
    ext = os.path.splitext(filename)[1]
    return f'bids/{instance.tender.id}/{instance.vendor.id}/commercial/proposal{ext}'


# ─────────────────────────────────────────────
# Custom Manager
# ─────────────────────────────────────────────
class BidManager(models.Manager):

    def for_tender(self, tender):
        return self.filter(tender=tender)

    def submitted(self):
        return self.filter(status=BidStatus.SUBMITTED)

    def under_review(self):
        return self.filter(status=BidStatus.UNDER_REVIEW)

    def shortlisted(self):
        return self.filter(status=BidStatus.SHORTLISTED)

    def approved(self):
        return self.filter(status=BidStatus.APPROVED)

    def by_vendor(self, vendor):
        return self.filter(vendor=vendor)


# ─────────────────────────────────────────────
# Bid Model
# ─────────────────────────────────────────────
class Bid(TimeStampedModel):
    """
    Represents a vendor's bid submission against a tender.
    One vendor can submit only one bid per tender.
    """

    tender            = models.ForeignKey(
                            Tender,
                            on_delete=models.PROTECT,
                            related_name='bids',
                            limit_choices_to={'status': 'open'},
                        )
    vendor            = models.ForeignKey(
                            Vendor,
                            on_delete=models.PROTECT,
                            related_name='bids',
                        )

    # Financial Proposal
    bid_amount        = models.DecimalField(
                            max_digits=15, decimal_places=2,
                            validators=[MinValueValidator(0.01)],
                            verbose_name=_('Bid Amount (INR)'),
                        )
    tax_percentage    = models.DecimalField(max_digits=5, decimal_places=2,
                                            default=0,
                                            verbose_name=_('Tax / GST (%)'))
    discount_percentage= models.DecimalField(max_digits=5, decimal_places=2,
                                             default=0,
                                             verbose_name=_('Discount (%)'))

    # Delivery & Warranty
    delivery_timeline_days = models.PositiveIntegerField(
                                 verbose_name=_('Delivery Timeline (Days)'),
                                 help_text='Number of days from PO date to delivery',
                             )
    warranty_period_months = models.PositiveIntegerField(
                                 verbose_name=_('Warranty Period (Months)'),
                                 default=0,
                             )

    # Documents
    technical_proposal = models.FileField(
                              upload_to=bid_technical_proposal_path,
                              null=True, blank=True,
                              help_text='Technical proposal document (PDF/Word)',
                          )
    commercial_proposal = models.FileField(
                              upload_to=bid_commercial_proposal_path,
                              null=True, blank=True,
                              help_text='Commercial / price proposal document',
                          )

    # Additional Information
    notes             = models.TextField(blank=True, null=True,
                                         help_text='Any additional notes or comments')
    is_compliant      = models.BooleanField(default=True,
                                            help_text='Vendor confirms compliance with tender requirements')

    # EMD Details
    emd_paid          = models.BooleanField(default=False,
                                            verbose_name=_('EMD Paid'))
    emd_reference     = models.CharField(max_length=100, blank=True, null=True,
                                         verbose_name=_('EMD Reference Number'))

    # Status & Workflow
    status            = models.CharField(
                            max_length=20,
                            choices=BidStatus.choices,
                            default=BidStatus.SUBMITTED,
                            db_index=True,
                        )
    submitted_at      = models.DateTimeField(auto_now_add=True)
    reviewed_by       = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='bids_reviewed',
                        )
    reviewed_at       = models.DateTimeField(null=True, blank=True)
    rejection_reason  = models.TextField(blank=True, null=True)
    internal_remarks  = models.TextField(blank=True, null=True)

    objects = BidManager()

    class Meta:
        verbose_name        = _('Bid')
        verbose_name_plural = _('Bids')
        ordering            = ['-submitted_at']
        unique_together     = [('tender', 'vendor')]  # One bid per vendor per tender
        indexes = [
            models.Index(fields=['tender', 'status']),
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Bid #{self.pk} — {self.vendor.company_name} → {self.tender.tender_number}"

    # ── Computed Fields ────────────────────────
    @property
    def total_bid_amount(self):
        """Bid amount after tax and discount."""
        taxed = self.bid_amount * (1 + self.tax_percentage / 100)
        discounted = taxed * (1 - self.discount_percentage / 100)
        return round(discounted, 2)

    @property
    def is_submitted(self):
        return self.status == BidStatus.SUBMITTED

    @property
    def is_winner(self):
        return self.status == BidStatus.APPROVED

    @property
    def has_technical_proposal(self):
        return bool(self.technical_proposal)

    @property
    def has_commercial_proposal(self):
        return bool(self.commercial_proposal)

    def can_be_withdrawn(self):
        """Vendor can withdraw only if tender is still open."""
        return (
            self.status in [BidStatus.SUBMITTED, BidStatus.UNDER_REVIEW]
            and self.tender.status == 'open'
        )

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('bids:detail', kwargs={'pk': self.pk})
