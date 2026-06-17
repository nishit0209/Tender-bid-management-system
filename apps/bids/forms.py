from django import forms
from .models import Bid

class BidSubmitForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = [
            'bid_amount', 'tax_percentage', 'discount_percentage',
            'delivery_timeline_days', 'warranty_period_months',
            'technical_proposal', 'commercial_proposal',
            'notes', 'emd_paid', 'emd_reference', 'is_compliant'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        emd_paid = cleaned_data.get('emd_paid')
        emd_reference = cleaned_data.get('emd_reference')

        if emd_paid and not emd_reference:
            self.add_error('emd_reference', 'EMD reference number is required if EMD is paid.')

        return cleaned_data
