from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class SimpleAppointmentBookingForm(forms.Form):
    """Simple form for booking appointments without model validation issues"""
    
    provider_type = forms.ChoiceField(
        choices=[
            ('nurse', 'Nurse'),
            ('psychologist', 'Psychologist'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    staff = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter staff based on provider type
        if 'provider_type' in self.data:
            try:
                provider_type = self.data.get('provider_type')
                self.fields['staff'].queryset = User.objects.filter(
                    role=provider_type, 
                    is_active=True
                ).order_by('first_name', 'last_name')
            except (ValueError, TypeError):
                self.fields['staff'].queryset = User.objects.none()
    
    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date and appointment_date < timezone.now().date():
            raise forms.ValidationError('Appointment date cannot be in the past.')
        return appointment_date
    
    def clean(self):
        cleaned_data = super().clean()
        staff = cleaned_data.get('staff')
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        
        # Basic validation
        if not staff:
            raise forms.ValidationError('Please select a staff member.')
        if not appointment_date:
            raise forms.ValidationError('Please select an appointment date.')
        if not appointment_time:
            raise forms.ValidationError('Please select an appointment time.')
        
        # Check for double booking
        from .models import Appointment
        if Appointment.objects.filter(
            staff=staff,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        ).exclude(status='cancelled').exists():
            raise forms.ValidationError('This time slot is already booked.')
        
        # Security/Penetration Test Fix: Verify slot is actually available in the schedule
        if staff and appointment_date and appointment_time:
            from apps.availability.models import Availability, BlockedPeriod
            from datetime import datetime
            
            day_of_week = appointment_date.isoweekday()
            
            # 1. Check if staff is available at all on this day
            availabilities = Availability.objects.filter(
                staff=staff,
                day_of_week=day_of_week,
                start_time__lte=appointment_time,
                end_time__gt=appointment_time,
                is_active=True
            )
            
            if not availabilities.exists():
                raise forms.ValidationError('The selected staff member is not available at this time.')
                
            # 2. Check if the time slot is blocked
            slot_datetime = timezone.make_aware(
                datetime.combine(appointment_date, appointment_time)
            )
            
            blocked = BlockedPeriod.objects.filter(
                staff=staff,
                start_datetime__lte=slot_datetime,
                end_datetime__gt=slot_datetime,
                is_active=True
            ).exists()
            
            if blocked:
                raise forms.ValidationError('The selected time slot is currently blocked or unavailable.')
                
        return cleaned_data
