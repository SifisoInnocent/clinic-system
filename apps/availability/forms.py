from django import forms
from django.core.exceptions import ValidationError
from .models import Availability, BlockedPeriod


class AvailabilityForm(forms.ModelForm):
    """Form for managing staff availability"""
    
    class Meta:
        model = Availability
        fields = ['day_of_week', 'start_time', 'end_time', 'is_active']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise ValidationError('Start time must be before end time.')
        
        # Check for minimum duration (30 minutes)
        if start_time and end_time:
            from datetime import datetime, timedelta
            duration = datetime.combine(datetime.min, end_time) - datetime.combine(datetime.min, start_time)
            if duration < timedelta(minutes=30):
                raise ValidationError('Availability duration must be at least 30 minutes.')


class AvailabilityBulkForm(forms.Form):
    """Form for bulk availability creation"""
    days = forms.MultipleChoiceField(
        choices=Availability.DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=True
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=True
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise ValidationError('Start time must be before end time.')


class BlockedPeriodForm(forms.ModelForm):
    """Form for creating blocked periods"""
    
    class Meta:
        model = BlockedPeriod
        fields = ['start_datetime', 'end_datetime', 'reason', 'is_active']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise ValidationError('Start datetime must be before end datetime.')
            
            # Check that start datetime is in the future
            from django.utils import timezone
            if start_datetime <= timezone.now():
                raise ValidationError('Start datetime must be in the future.')
            
            # Check minimum duration (30 minutes)
            from datetime import timedelta
            if (end_datetime - start_datetime) < timedelta(minutes=30):
                raise ValidationError('Blocked period must be at least 30 minutes long.')
