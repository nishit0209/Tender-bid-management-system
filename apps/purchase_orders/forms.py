from django import forms
from .models import PurchaseOrder

class POCreateForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            'tax_amount', 
            'delivery_date', 
            'delivery_address', 
            'delivery_instructions',
            'terms_and_conditions',
            'payment_terms',
            'penalty_clause'
        ]
        widgets = {
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'delivery_address': forms.Textarea(attrs={'rows': 3}),
            'delivery_instructions': forms.Textarea(attrs={'rows': 2}),
            'terms_and_conditions': forms.Textarea(attrs={'rows': 4}),
            'payment_terms': forms.TextInput(),
            'penalty_clause': forms.Textarea(attrs={'rows': 2}),
        }

class PODeliveryForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['delivery_proof']
