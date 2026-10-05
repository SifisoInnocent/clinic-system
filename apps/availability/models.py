from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import User


class Availability(models.Model):
    DAY_CHOICES = [
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday'),
    ]
    
    staff = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='availabilities'
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    session_length = models.IntegerField(default=60, help_text="Session length in minutes")
    buffer_time = models.IntegerField(default=15, help_text="Buffer time between sessions in minutes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'availability'
        unique_together = ['staff', 'day_of_week', 'start_time', 'end_time']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.get_day_of_week_display()} {self.start_time} to {self.end_time}"
    
    def clean(self):
        # Validate that staff is actually staff
        if hasattr(self, 'staff_id') and self.staff_id and not self.staff.is_staff_user():
            raise ValidationError("Selected user is not staff (nurse or psychologist)")
        
        # Validate time range
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
        
        # Check for overlapping availability
        if hasattr(self, 'staff_id') and self.staff_id and self.day_of_week and self.start_time and self.end_time:
            overlapping = Availability.objects.filter(
                staff=self.staff,
                day_of_week=self.day_of_week,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
                is_active=True
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError("This time range overlaps with existing availability")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class BlockedPeriod(models.Model):
    """Temporary blocks in staff availability (vacation, sick leave, etc.)"""
    staff = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='blocked_periods',
        limit_choices_to={'role__in': ['nurse', 'psychologist']}
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    reason = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'blocked_periods'
        ordering = ['start_datetime']
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.reason} ({self.start_datetime} to {self.end_datetime})"
    
    def clean(self):
        # Validate that staff is actually staff
        if hasattr(self, 'staff_id') and self.staff_id and not self.staff.is_staff_user():
            raise ValidationError("Selected user is not staff (nurse or psychologist)")
        
        # Validate datetime range
        if self.start_datetime and self.end_datetime and self.start_datetime >= self.end_datetime:
            raise ValidationError("Start datetime must be before end datetime")
        
        # Check for overlapping blocked periods
        if hasattr(self, 'staff_id') and self.staff_id and self.start_datetime and self.end_datetime:
            overlapping = BlockedPeriod.objects.filter(
                staff=self.staff,
                start_datetime__lt=self.end_datetime,
                end_datetime__gt=self.start_datetime,
                is_active=True
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                raise ValidationError("This time range overlaps with existing blocked period")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_current(self):
        """Check if blocked period is currently active"""
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime and self.is_active
    
    def is_future(self):
        """Check if blocked period is in the future"""
        return self.start_datetime > timezone.now() and self.is_active
    
    def is_past(self):
        """Check if blocked period has ended"""
        return self.end_datetime < timezone.now()
