from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('nurse', 'Nurse'),
        ('psychologist', 'Psychologist'),
        ('admin', 'Administrator'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    student_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_locked = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        if self.role == 'student':
            return f"{self.student_number} - {self.get_full_name()}"
        else:
            return f"{self.employee_id} - {self.get_full_name()}"
    
    def is_student(self):
        return self.role == 'student'
    
    def is_nurse(self):
        return self.role == 'nurse'
    
    def is_psychologist(self):
        return self.role == 'psychologist'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_staff_user(self):
        return self.role in ['nurse', 'psychologist']
    
    def can_login(self):
        """Check if user can login (enforces lockout after 5 failed attempts)"""
        if self.is_locked:
            if self.locked_until and self.locked_until > timezone.now():
                return False
            else:
                # Lockout period expired, unlock account
                self.is_locked = False
                self.failed_login_attempts = 0
                self.locked_until = None
                self.save()
        return True
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock after 5 attempts"""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.is_locked = True
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        
        self.save()
    
    def reset_failed_login(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.is_locked = False
        self.locked_until = None
        self.save()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    medical_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} Profile"
