from django import forms
from .models import Tender, TenderStatus, TenderCategory

class TenderFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search tenders...'}))
    status = forms.ChoiceField(choices=[('', 'All Statuses')] + TenderStatus.choices, required=False)
    category = forms.ChoiceField(choices=[('', 'All Categories')] + TenderCategory.choices, required=False)

class TenderCreateForm(forms.ModelForm):
    class Meta:
        model = Tender
        fields = [
            'title', 'description', 'category', 'custom_category', 'tender_type',
            'quantity', 'unit', 'specifications',
            'estimated_budget', 'emd_amount',
            'opening_date', 'closing_date', 'evaluation_date', 'delivery_deadline',
            'terms_and_conditions', 'eligibility_criteria',
            'is_pre_bid_meeting_required', 'pre_bid_meeting_date', 'pre_bid_meeting_location',
            'tender_document', 'is_public'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'specifications': forms.Textarea(attrs={'rows': 4}),
            'terms_and_conditions': forms.Textarea(attrs={'rows': 4}),
            'eligibility_criteria': forms.Textarea(attrs={'rows': 3}),
            'opening_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'closing_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'evaluation_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'delivery_deadline': forms.DateInput(attrs={'type': 'date'}),
            'pre_bid_meeting_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        opening_date = cleaned_data.get('opening_date')
        closing_date = cleaned_data.get('closing_date')
        evaluation_date = cleaned_data.get('evaluation_date')
        is_pre_bid_required = cleaned_data.get('is_pre_bid_meeting_required')
        pre_bid_date = cleaned_data.get('pre_bid_meeting_date')
        pre_bid_location = cleaned_data.get('pre_bid_meeting_location')
        category = cleaned_data.get('category')
        custom_category = cleaned_data.get('custom_category')

        if category == 'other' and not custom_category:
            self.add_error('custom_category', 'Please specify the category name.')

        if opening_date and closing_date and opening_date >= closing_date:
            self.add_error('closing_date', 'Closing date must be after opening date.')

        if closing_date and evaluation_date and evaluation_date <= closing_date:
            self.add_error('evaluation_date', 'Evaluation date must be after closing date.')

        if is_pre_bid_required:
            if not pre_bid_date:
                self.add_error('pre_bid_meeting_date', 'Pre-bid meeting date is required if meeting is required.')
            if not pre_bid_location:
                self.add_error('pre_bid_meeting_location', 'Location is required if pre-bid meeting is required.')

        return cleaned_data


class TenderApprovalForm(forms.Form):
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional remarks...'}),
        required=False
    )
