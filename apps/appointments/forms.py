from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Appointment, AppointmentHistory
from apps.accounts.models import User


class AppointmentBookingForm(forms.ModelForm):
    """Form for booking new appointments"""
    
    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
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
        else:
            self.fields['staff'].queryset = User.objects.none()
    
    class Meta:
        model = Appointment
        fields = ['provider_type', 'staff', 'appointment_date', 'appointment_time', 'reason']
        exclude = ['student']
        widgets = {
            'provider_type': forms.Select(attrs={'class': 'form-control'}),
            'staff': forms.Select(attrs={'class': 'form-control'}),
            'appointment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date and appointment_date < timezone.now().date():
            raise ValidationError('Appointment date cannot be in the past.')
        return appointment_date
    
    def clean(self):
        cleaned_data = super().clean()
        staff = cleaned_data.get('staff')
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        
        # Basic validation
        if not staff:
            raise ValidationError('Please select a staff member.')
        if not appointment_date:
            raise ValidationError('Please select an appointment date.')
        if not appointment_time:
            raise ValidationError('Please select an appointment time.')
        
        # Check if appointment date is in the past
        if appointment_date < timezone.now().date():
            raise ValidationError('Appointment date cannot be in the past.')
        
        # Skip duplicate appointment check for now to avoid student field issues
        # TODO: Add proper duplicate checking after student assignment
        
        return cleaned_data


class AppointmentRescheduleForm(forms.ModelForm):
    """Form for rescheduling appointments"""
    
    def __init__(self, *args, **kwargs):
        self.appointment = kwargs.pop('appointment', None)
        super().__init__(*args, **kwargs)
        
        if self.appointment:
            self.fields['staff'].queryset = User.objects.filter(
                role=self.appointment.provider_type,
                is_active=True
            ).order_by('first_name', 'last_name')
    
    class Meta:
        model = Appointment
        fields = ['staff', 'appointment_date', 'appointment_time']
        widgets = {
            'staff': forms.Select(attrs={'class': 'form-control'}),
            'appointment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }
    
    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date and appointment_date < timezone.now().date():
            raise ValidationError('Appointment date cannot be in the past.')
        return appointment_date
    
    def clean(self):
        cleaned_data = super().clean()
        staff = cleaned_data.get('staff')
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        
        if staff and appointment_date and appointment_time:
            from apps.availability.models import Availability, BlockedPeriod
            
            # Check day of week availability
            day_of_week = appointment_date.isoweekday()
            if day_of_week > 5:  # Weekend
                raise ValidationError('Appointments are only available on weekdays.')
            
            # Check staff availability
            availability = Availability.objects.filter(
                staff=staff,
                day_of_week=day_of_week,
                is_active=True,
                start_time__lte=appointment_time,
                end_time__gte=appointment_time
            ).first()
            
            if not availability:
                raise ValidationError('Staff is not available at the selected time.')
            
            # Check for blocked periods
            appointment_datetime = timezone.make_aware(
                timezone.datetime.combine(appointment_date, appointment_time)
            )
            
            blocked = BlockedPeriod.objects.filter(
                staff=staff,
                start_datetime__lte=appointment_datetime,
                end_datetime__gte=appointment_datetime,
                is_active=True
            ).exists()
            
            if blocked:
                raise ValidationError('Staff is not available during this period.')
            
            # Check for existing appointments (exclude current appointment)
            existing = Appointment.objects.filter(
                staff=staff,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['pending', 'confirmed']
            ).exclude(pk=self.appointment.pk).exists()
            
            if existing:
                raise ValidationError('This time slot is already booked.')


class AppointmentStatusUpdateForm(forms.ModelForm):
    """Form for updating appointment status (staff use)"""
    
    class Meta:
        model = Appointment
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter status choices based on current status
        if self.instance and self.instance.status == 'confirmed':
            self.fields['status'].choices = [
                ('confirmed', 'Confirmed'),
                ('completed', 'Completed'),
                ('cancelled', 'Cancelled'),
                ('no_show', 'No-Show'),
            ]
        elif self.instance and self.instance.status == 'pending':
            self.fields['status'].choices = [
                ('pending', 'Pending'),
                ('confirmed', 'Confirmed'),
                ('cancelled', 'Cancelled'),
            ]
        else:
            # For completed, cancelled, or no-show appointments
            self.fields['status'].choices = [
                (self.instance.status, self.instance.get_status_display()),
            ]
            self.fields['status'].widget.attrs['disabled'] = True


class AppointmentSearchForm(forms.Form):
    """Form for searching appointments"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by student name or ID'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Appointment.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError('Date from cannot be after date to.')
