"""
Vendors App — Forms
Enterprise Tender & Bid Management System
"""

from django import forms
from django.core.validators import FileExtensionValidator
from .models import Vendor, VendorDocument, DocumentType, VendorStatus


# ─────────────────────────────────────────────
# Vendor Registration Form
# ─────────────────────────────────────────────
class VendorRegistrationForm(forms.ModelForm):
    """
    Used by vendor users to register their company.
    Split into sections: Company, Contact, Address, Business, Bank.
    """

    class Meta:
        model = Vendor
        fields = [
            # Company
            'company_name', 'gst_number', 'pan_number', 'cin_number', 'msme_number',
            # Contact
            'contact_person', 'contact_email', 'contact_phone', 'alternate_phone', 'website',
            # Address
            'address_line1', 'address_line2', 'city', 'state', 'pincode', 'country',
            # Business
            'business_type', 'year_established', 'annual_turnover', 'employee_count', 'category_of_goods',
            # Bank
            'bank_name', 'bank_account_number', 'bank_ifsc', 'bank_branch',
        ]
        widgets = {
            'company_name':       forms.TextInput(attrs={'placeholder': 'e.g. Acme Technologies Pvt. Ltd.'}),
            'gst_number':         forms.TextInput(attrs={'placeholder': '15-digit GST number', 'maxlength': '15', 'class': 'uppercase'}),
            'pan_number':         forms.TextInput(attrs={'placeholder': '10-digit PAN number', 'maxlength': '10', 'class': 'uppercase'}),
            'cin_number':         forms.TextInput(attrs={'placeholder': 'e.g. U74999MH2010PTC123456'}),
            'msme_number':        forms.TextInput(attrs={'placeholder': 'MSME / Udyam Registration Number'}),
            'contact_person':     forms.TextInput(attrs={'placeholder': 'Full name of contact person'}),
            'contact_email':      forms.EmailInput(attrs={'placeholder': 'email@company.com'}),
            'contact_phone':      forms.TextInput(attrs={'placeholder': '+91 98765 43210'}),
            'alternate_phone':    forms.TextInput(attrs={'placeholder': 'Optional alternate number'}),
            'website':            forms.URLInput(attrs={'placeholder': 'https://www.company.com'}),
            'address_line1':      forms.TextInput(attrs={'placeholder': 'Street address, building number'}),
            'address_line2':      forms.TextInput(attrs={'placeholder': 'Area, landmark (optional)'}),
            'city':               forms.TextInput(attrs={'placeholder': 'City'}),
            'state':              forms.TextInput(attrs={'placeholder': 'State'}),
            'pincode':            forms.TextInput(attrs={'placeholder': '6-digit PIN code', 'maxlength': '6'}),
            'country':            forms.TextInput(attrs={'placeholder': 'Country'}),
            'business_type':      forms.TextInput(attrs={'placeholder': 'e.g. Manufacturer, Trader, Service Provider'}),
            'year_established':   forms.NumberInput(attrs={'placeholder': 'e.g. 2005', 'min': '1900', 'max': '2025'}),
            'annual_turnover':    forms.NumberInput(attrs={'placeholder': 'Annual turnover in INR', 'step': '0.01'}),
            'employee_count':     forms.NumberInput(attrs={'placeholder': 'Number of employees', 'min': '1'}),
            'category_of_goods':  forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe your products/services...'}),
            'bank_name':          forms.TextInput(attrs={'placeholder': 'e.g. State Bank of India'}),
            'bank_account_number':forms.TextInput(attrs={'placeholder': 'Bank account number'}),
            'bank_ifsc':          forms.TextInput(attrs={'placeholder': '11-character IFSC code', 'maxlength': '11', 'class': 'uppercase'}),
            'bank_branch':        forms.TextInput(attrs={'placeholder': 'Branch name and city'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # All fields get common CSS class
        for field_name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'form-input {existing}'.strip()
        # Optional fields
        optional = [
            'cin_number', 'msme_number', 'alternate_phone', 'website',
            'address_line2', 'business_type', 'year_established',
            'annual_turnover', 'employee_count', 'category_of_goods',
            'bank_name', 'bank_account_number', 'bank_ifsc', 'bank_branch',
        ]
        for f in optional:
            self.fields[f].required = False

    def clean_gst_number(self):
        gst = self.cleaned_data.get('gst_number', '').upper().strip()
        if len(gst) != 15:
            raise forms.ValidationError('GST number must be exactly 15 characters.')
        return gst

    def clean_pan_number(self):
        pan = self.cleaned_data.get('pan_number', '').upper().strip()
        if len(pan) != 10:
            raise forms.ValidationError('PAN number must be exactly 10 characters.')
        return pan

    def clean_bank_ifsc(self):
        ifsc = self.cleaned_data.get('bank_ifsc', '')
        if ifsc:
            ifsc = ifsc.upper().strip()
            if len(ifsc) != 11:
                raise forms.ValidationError('IFSC code must be exactly 11 characters.')
        return ifsc

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode', '').strip()
        if pincode and not pincode.isdigit():
            raise forms.ValidationError('PIN code must contain only digits.')
        return pincode


# ─────────────────────────────────────────────
# Vendor Update Form (same fields, optional PAN/GST edit)
# ─────────────────────────────────────────────
class VendorUpdateForm(VendorRegistrationForm):
    """
    Edit existing vendor profile.
    Excludes GST/PAN (read-only after registration to maintain uniqueness).
    """
    class Meta(VendorRegistrationForm.Meta):
        exclude = ['gst_number', 'pan_number']
        fields = [f for f in VendorRegistrationForm.Meta.fields
                  if f not in ('gst_number', 'pan_number')]


# ─────────────────────────────────────────────
# Document Upload Form
# ─────────────────────────────────────────────
class DocumentUploadForm(forms.ModelForm):

    class Meta:
        model = VendorDocument
        fields = ['document_type', 'document_name', 'file', 'valid_from', 'valid_until']
        widgets = {
            'document_type':  forms.Select(),
            'document_name':  forms.TextInput(attrs={'placeholder': 'e.g. GST Certificate 2024'}),
            'valid_from':     forms.DateInput(attrs={'type': 'date'}),
            'valid_until':    forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-input'
        self.fields['document_name'].required = False
        self.fields['valid_from'].required = False
        self.fields['valid_until'].required = False
        self.fields['file'].validators = [
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'])
        ]
        self.fields['file'].help_text = 'Allowed: PDF, JPG, PNG, DOC, DOCX. Max size: 5 MB.'

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            max_size = 5 * 1024 * 1024  # 5 MB
            if file.size > max_size:
                raise forms.ValidationError('File size must not exceed 5 MB.')
        return file


# ─────────────────────────────────────────────
# Vendor Reject / Suspend Form
# ─────────────────────────────────────────────
class VendorRejectForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Provide a detailed reason for rejection...',
            'class': 'form-input',
        }),
        min_length=20,
        label='Rejection Reason',
        help_text='Minimum 20 characters. This will be visible to the vendor.',
    )


class VendorSuspendForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Provide reason for suspension...',
            'class': 'form-input',
        }),
        min_length=20,
        label='Suspension Reason',
    )


# ─────────────────────────────────────────────
# Document Rejection Form
# ─────────────────────────────────────────────
class DocumentRejectForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Reason for document rejection...',
            'class': 'form-input',
        }),
        min_length=10,
        label='Rejection Reason',
    )


# ─────────────────────────────────────────────
# Vendor Filter / Search Form
# ─────────────────────────────────────────────
class VendorFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'All Status')] + VendorStatus.choices

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by company, GST, PAN...',
            'class': 'form-input',
        }),
        label='Search',
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'}),
        label='Status',
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Filter by city', 'class': 'form-input'}),
        label='City',
    )
    state = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Filter by state', 'class': 'form-input'}),
        label='State',
    )
