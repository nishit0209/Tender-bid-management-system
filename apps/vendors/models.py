"""
Vendor & VendorDocument Models — Vendors App
Enterprise Tender & Bid Management System
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.accounts.models import TimeStampedModel
import os


# ─────────────────────────────────────────────
# Choices
# ─────────────────────────────────────────────
class VendorStatus(models.TextChoices):
    PENDING   = 'pending',   _('Pending Review')
    VERIFIED  = 'verified',  _('Verified by Procurement')
    APPROVED  = 'approved',  _('Approved by Manager')
    REJECTED  = 'rejected',  _('Rejected')
    SUSPENDED = 'suspended', _('Suspended')


class DocumentType(models.TextChoices):
    GST_CERTIFICATE     = 'gst_certificate',     _('GST Certificate')
    PAN_CARD            = 'pan_card',             _('PAN Card')
    COMPANY_REGISTRATION= 'company_registration', _('Company Registration Certificate')
    BANK_DETAILS        = 'bank_details',         _('Bank Details / Cancelled Cheque')
    ISO_CERTIFICATE     = 'iso_certificate',      _('ISO Certificate')
    EXPERIENCE_CERTIFICATE = 'experience_certificate', _('Experience Certificate')
    FINANCIAL_STATEMENT = 'financial_statement',  _('Financial Statement')
    OTHER               = 'other',                _('Other')


class DocumentStatus(models.TextChoices):
    PENDING  = 'pending',  _('Pending Review')
    VERIFIED = 'verified', _('Verified')
    REJECTED = 'rejected', _('Rejected')


# ─────────────────────────────────────────────
# Custom Manager
# ─────────────────────────────────────────────
class VendorManager(models.Manager):

    def pending(self):
        return self.filter(status=VendorStatus.PENDING)

    def verified(self):
        return self.filter(status=VendorStatus.VERIFIED)

    def approved(self):
        return self.filter(status=VendorStatus.APPROVED)

    def active(self):
        return self.filter(status=VendorStatus.APPROVED, user__is_active=True)

    def rejected(self):
        return self.filter(status=VendorStatus.REJECTED)

    def suspended(self):
        return self.filter(status=VendorStatus.SUSPENDED)


# ─────────────────────────────────────────────
# Upload Paths
# ─────────────────────────────────────────────
def vendor_document_upload_path(instance, filename):
    """Upload vendor documents to: vendors/<vendor_id>/documents/<doc_type>/<filename>"""
    ext = os.path.splitext(filename)[1]
    safe_name = f"{instance.document_type}{ext}"
    return f'vendors/{instance.vendor.id}/documents/{instance.document_type}/{safe_name}'


# ─────────────────────────────────────────────
# Vendor Model
# ─────────────────────────────────────────────
class Vendor(TimeStampedModel):
    """
    Represents a vendor/supplier organization registered in the system.
    Each vendor is linked to a CustomUser with role='vendor'.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='vendor_profile',
        # No limit_choices_to so admin can assign any user
    )

    # Company Information
    company_name       = models.CharField(max_length=255, db_index=True)
    gst_number         = models.CharField(max_length=15, unique=True, verbose_name=_('GST Number'))
    pan_number         = models.CharField(max_length=10, unique=True, verbose_name=_('PAN Number'))
    cin_number         = models.CharField(max_length=21, blank=True, null=True, unique=True,
                                          verbose_name=_('CIN Number'))
    msme_number        = models.CharField(max_length=50, blank=True, null=True,
                                          verbose_name=_('MSME Registration Number'))

    # Contact Information
    contact_person     = models.CharField(max_length=100)
    contact_email      = models.EmailField()
    contact_phone      = models.CharField(max_length=15)
    alternate_phone    = models.CharField(max_length=15, blank=True, null=True)
    website            = models.URLField(blank=True, null=True)

    # Address
    address_line1      = models.CharField(max_length=255)
    address_line2      = models.CharField(max_length=255, blank=True, null=True)
    city               = models.CharField(max_length=100)
    state              = models.CharField(max_length=100)
    pincode            = models.CharField(max_length=10)
    country            = models.CharField(max_length=100, default='India')

    # Business Information
    business_type      = models.CharField(max_length=100, blank=True, null=True,
                                          help_text='e.g. Manufacturer, Trader, Service Provider')
    year_established   = models.PositiveIntegerField(blank=True, null=True)
    annual_turnover    = models.DecimalField(max_digits=15, decimal_places=2,
                                             blank=True, null=True,
                                             help_text='Annual turnover in INR')
    employee_count     = models.PositiveIntegerField(blank=True, null=True)
    category_of_goods  = models.TextField(blank=True, null=True,
                                          help_text='Categories / types of goods or services offered')

    # Bank Details
    bank_name          = models.CharField(max_length=100, blank=True, null=True)
    bank_account_number= models.CharField(max_length=30, blank=True, null=True)
    bank_ifsc          = models.CharField(max_length=11, blank=True, null=True, verbose_name=_('IFSC Code'))
    bank_branch        = models.CharField(max_length=100, blank=True, null=True)

    # Status & Workflow
    status             = models.CharField(
                             max_length=20,
                             choices=VendorStatus.choices,
                             default=VendorStatus.PENDING,
                             db_index=True,
                         )
    rejection_reason   = models.TextField(blank=True, null=True)
    suspension_reason  = models.TextField(blank=True, null=True)
    document_retries_left = models.PositiveIntegerField(default=5, help_text='Number of document re-upload attempts allowed')

    # Workflow Tracking
    submitted_at       = models.DateTimeField(auto_now_add=True)
    verified_by        = models.ForeignKey(
                             settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL,
                             null=True, blank=True,
                             related_name='vendors_verified',
                             limit_choices_to={'role': 'procurement_officer'},
                         )
    verified_at        = models.DateTimeField(null=True, blank=True)
    approved_by        = models.ForeignKey(
                             settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL,
                             null=True, blank=True,
                             related_name='vendors_approved',
                             limit_choices_to={'role': 'manager'},
                         )
    approved_at        = models.DateTimeField(null=True, blank=True)

    # Notes
    internal_notes     = models.TextField(blank=True, null=True,
                                          help_text='Internal notes visible only to staff')

    objects = VendorManager()

    class Meta:
        verbose_name        = _('Vendor')
        verbose_name_plural = _('Vendors')
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['company_name']),
            models.Index(fields=['gst_number']),
            models.Index(fields=['pan_number']),
        ]

    def __str__(self):
        return f"{self.company_name} [{self.get_status_display()}]"

    # ── Properties ────────────────────────────
    @property
    def is_active(self):
        return self.status == VendorStatus.APPROVED

    @property
    def is_pending(self):
        return self.status == VendorStatus.PENDING

    @property
    def full_address(self):
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts += [self.city, self.state, self.pincode, self.country]
        return ', '.join(filter(None, parts))

    @property
    def documents_count(self):
        return self.documents.count()

    @property
    def verified_documents_count(self):
        return self.documents.filter(status=DocumentStatus.VERIFIED).count()

    @property
    def all_required_documents_verified(self):
        """Check if all mandatory documents are verified."""
        required_types = [
            DocumentType.GST_CERTIFICATE,
            DocumentType.PAN_CARD,
            DocumentType.COMPANY_REGISTRATION,
            DocumentType.BANK_DETAILS,
        ]
        return all(
            self.documents.filter(
                document_type=doc_type,
                status=DocumentStatus.VERIFIED
            ).exists()
            for doc_type in required_types
        )

    @property
    def completion_percentage(self):
        """Profile completion percentage (0-100)."""
        fields_to_check = [
            self.company_name, self.gst_number, self.pan_number,
            self.contact_person, self.contact_email, self.contact_phone,
            self.address_line1, self.city, self.state, self.pincode,
            self.bank_name, self.bank_account_number, self.bank_ifsc,
        ]
        filled = sum(1 for f in fields_to_check if f)
        return int((filled / len(fields_to_check)) * 100)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('vendors:detail', kwargs={'pk': self.pk})

    def can_submit_bids(self):
        """Vendor can only submit bids if approved."""
        return self.status == VendorStatus.APPROVED and self.user.is_active


# ─────────────────────────────────────────────
# VendorDocument Model
# ─────────────────────────────────────────────
class VendorDocument(TimeStampedModel):
    """
    Represents a document uploaded by a vendor.
    Supports PDF, images, Word documents, and Excel files.
    """

    vendor        = models.ForeignKey(
                        Vendor,
                        on_delete=models.CASCADE,
                        related_name='documents',
                    )
    document_type = models.CharField(
                        max_length=50,
                        choices=DocumentType.choices,
                        db_index=True,
                    )
    document_name = models.CharField(max_length=255, blank=True, null=True,
                                     help_text='Optional friendly name for the document')
    file          = models.FileField(upload_to=vendor_document_upload_path)
    file_size     = models.PositiveIntegerField(null=True, blank=True,
                                                help_text='File size in bytes')

    # Verification
    status        = models.CharField(
                        max_length=20,
                        choices=DocumentStatus.choices,
                        default=DocumentStatus.PENDING,
                        db_index=True,
                    )
    verified_by   = models.ForeignKey(
                        settings.AUTH_USER_MODEL,
                        on_delete=models.SET_NULL,
                        null=True, blank=True,
                        related_name='documents_verified',
                    )
    verified_at   = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    remarks       = models.TextField(blank=True, null=True,
                                     help_text='Internal remarks by verifier')
    ai_confidence_score = models.IntegerField(null=True, blank=True)
    ai_analysis_remarks = models.TextField(blank=True, null=True)

    # Validity
    valid_from    = models.DateField(null=True, blank=True)
    valid_until   = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name        = _('Vendor Document')
        verbose_name_plural = _('Vendor Documents')
        ordering            = ['-created_at']
        unique_together     = [('vendor', 'document_type')]
        indexes = [
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['document_type', 'status']),
        ]

    def __str__(self):
        return f"{self.vendor.company_name} — {self.get_document_type_display()} [{self.get_status_display()}]"

    @property
    def filename(self):
        return os.path.basename(self.file.name) if self.file else None

    @property
    def file_extension(self):
        if self.file:
            return os.path.splitext(self.file.name)[1].lower()
        return None

    @property
    def is_image(self):
        return self.file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    @property
    def is_pdf(self):
        return self.file_extension == '.pdf'

    @property
    def is_verified(self):
        return self.status == DocumentStatus.VERIFIED

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('vendors:document_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # Auto-capture file size on save
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size
        super().save(*args, **kwargs)
