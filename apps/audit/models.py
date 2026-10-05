from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create_user', 'Create User'),
        ('update_user', 'Update User'),
        ('deactivate_user', 'Deactivate User'),
        ('delete_user', 'Delete User'),
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('failed_login', 'Failed Login'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
        ('password_reset', 'Password Reset'),
        ('create_appointment', 'Create Appointment'),
        ('update_appointment', 'Update Appointment'),
        ('cancel_appointment', 'Cancel Appointment'),
        ('reschedule_appointment', 'Reschedule Appointment'),
        ('complete_appointment', 'Complete Appointment'),
        ('mark_no_show', 'Mark No-Show'),
        ('create_availability', 'Create Availability'),
        ('update_availability', 'Update Availability'),
        ('delete_availability', 'Delete Availability'),
        ('create_blocked_period', 'Create Blocked Period'),
        ('update_blocked_period', 'Update Blocked Period'),
        ('delete_blocked_period', 'Delete Blocked Period'),
        ('generate_report', 'Generate Report'),
        ('export_data', 'Export Data'),
        ('system_config', 'System Configuration'),
        ('access_patient_record', 'Access Patient Record'),
    ]
    
    admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='audit_actions'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target_user = models.CharField(max_length=150, blank=True)  # Username or ID of target
    target_object = models.CharField(max_length=150, blank=True)  # Object type and ID
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} by {self.admin} at {self.timestamp}"
    
    @classmethod
    def log_action(cls, admin, action, target_user='', target_object='', description='', ip_address=None, user_agent=''):
        """Create an audit log entry"""
        return cls.objects.create(
            admin=admin,
            action=action,
            target_user=target_user,
            target_object=target_object,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
