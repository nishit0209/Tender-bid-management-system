from django import forms
from django.core.exceptions import ValidationError
from .models import Evaluation

class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = [
            'price_score', 'price_remarks',
            'experience_score', 'experience_remarks',
            'warranty_score', 'warranty_remarks',
            'delivery_score', 'delivery_remarks',
            'overall_remarks'
        ]
        widgets = {
            'price_remarks': forms.Textarea(attrs={'rows': 2}),
            'experience_remarks': forms.Textarea(attrs={'rows': 2}),
            'warranty_remarks': forms.Textarea(attrs={'rows': 2}),
            'delivery_remarks': forms.Textarea(attrs={'rows': 2}),
            'overall_remarks': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_price_score(self):
        score = self.cleaned_data.get('price_score')
        if score is not None and (score < 0 or score > 40):
            raise ValidationError('Price score must be between 0 and 40.')
        return score

    def clean_experience_score(self):
        score = self.cleaned_data.get('experience_score')
        if score is not None and (score < 0 or score > 30):
            raise ValidationError('Experience score must be between 0 and 30.')
        return score

    def clean_warranty_score(self):
        score = self.cleaned_data.get('warranty_score')
        if score is not None and (score < 0 or score > 20):
            raise ValidationError('Warranty score must be between 0 and 20.')
        return score

    def clean_delivery_score(self):
        score = self.cleaned_data.get('delivery_score')
        if score is not None and (score < 0 or score > 10):
            raise ValidationError('Delivery score must be between 0 and 10.')
        return score
