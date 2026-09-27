from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.appointments.models import Appointment


class NotificationLog(models.Model):
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    PURPOSE_CHOICES = [
        ('booking', 'Booking Confirmation'),
        ('cancellation', 'Cancellation Notice'),
        ('reschedule', 'Reschedule Confirmation'),
        ('reminder', 'Appointment Reminder'),
        ('no_show', 'No-Show Notice'),
        ('completed', 'Completion Notice'),
        ('password_reset', 'Password Reset'),
    ]
    
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    recipient = models.CharField(max_length=200)  # Email address or phone number
    appointment = models.ForeignKey(
        Appointment, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='notifications'
    )
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.get_purpose_display()} - {self.recipient}"
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message):
        """Mark notification as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.save()


class NotificationTemplate(models.Model):
    """Email and SMS templates"""
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]
    
    PURPOSE_CHOICES = [
        ('booking', 'Booking Confirmation'),
        ('cancellation', 'Cancellation Notice'),
        ('reschedule', 'Reschedule Confirmation'),
        ('reminder', 'Appointment Reminder'),
        ('no_show', 'No-Show Notice'),
        ('completed', 'Completion Notice'),
        ('password_reset', 'Password Reset'),
    ]
    
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    subject_template = models.CharField(max_length=200, blank=True)
    message_template = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
        unique_together = ['type', 'purpose']
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.get_purpose_display()}"
    
    def render_subject(self, context):
        """Render subject template with context"""
        if self.subject_template:
            from django.template import Template, Context
            template = Template(self.subject_template)
            return template.render(Context(context))
        return ""
    
    def render_message(self, context):
        """Render message template with context"""
        from django.template import Template, Context
        template = Template(self.message_template)
        return template.render(Context(context))
