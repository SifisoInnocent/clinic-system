from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.accounts.models import User


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No-Show'),
    ]
    
    PROVIDER_TYPE_CHOICES = [
        ('nurse', 'Nurse'),
        ('psychologist', 'Psychologist'),
    ]
    
    appointment_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_appointments'
    )
    staff = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='staff_appointments'
    )
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPE_CHOICES)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notification_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'appointments'
        ordering = ['appointment_date', 'appointment_time']
        unique_together = ['staff', 'appointment_date', 'appointment_time']
    
    def __str__(self):
        return f"Appointment {self.appointment_id}: {self.student.get_full_name()} with {self.staff.get_full_name()} on {self.appointment_date} at {self.appointment_time}"
    
    @property
    def id(self):
        """Backwards compatibility for references using .id instead of .appointment_id"""
        return self.appointment_id
    
    def clean(self):
        # Validate that student is actually a student
        if hasattr(self, 'student_id') and self.student_id and not self.student.is_student():
            raise ValidationError("Selected user is not a student")
        
        # Validate that staff is actually staff
        if hasattr(self, 'staff_id') and self.staff_id and not self.staff.is_staff_user():
            raise ValidationError("Selected user is not staff (nurse or psychologist)")
        
        # Validate provider type matches staff role
        if hasattr(self, 'staff_id') and self.staff_id and self.provider_type:
            if self.provider_type == 'nurse' and not self.staff.is_nurse():
                raise ValidationError("Provider type 'Nurse' does not match staff role")
            if self.provider_type == 'psychologist' and not self.staff.is_psychologist():
                raise ValidationError("Provider type 'Psychologist' does not match staff role")
        
        # Check for double booking
        if hasattr(self, 'staff_id') and self.staff_id and self.appointment_date and self.appointment_time:
            existing = Appointment.objects.filter(
                staff=self.staff,
                appointment_date=self.appointment_date,
                appointment_time=self.appointment_time,
                status__in=['pending', 'confirmed']
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError("This time slot is already booked")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_past(self):
        """Check if appointment time has passed"""
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.appointment_time)
        )
        return timezone.now() > appointment_datetime
    
    def is_upcoming(self):
        """Check if appointment is in the future"""
        return not self.is_past()
    
    def can_be_cancelled(self):
        """Check if appointment can be cancelled"""
        return self.status in ['pending', 'confirmed'] and self.is_upcoming()
    
    def can_be_rescheduled(self):
        """Check if appointment can be rescheduled"""
        return self.can_be_cancelled()
    
    def mark_as_no_show(self):
        """Mark appointment as no-show"""
        if self.status == 'confirmed' and self.is_past():
            self.status = 'no_show'
            self.save()
    
    def get_datetime(self):
        """Get appointment as datetime object"""
        return timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.appointment_time)
        )


class AppointmentHistory(models.Model):
    """Track changes to appointments"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50)  # created, cancelled, rescheduled, completed, no_show
    old_status = models.CharField(max_length=20, null=True, blank=True)
    new_status = models.CharField(max_length=20, null=True, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'appointment_history'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Appointment {self.appointment.appointment_id} - {self.action} by {self.changed_by}"
