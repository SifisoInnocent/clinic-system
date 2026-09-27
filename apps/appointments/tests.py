from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse

from .models import Appointment, AppointmentHistory
from apps.availability.models import Availability

User = get_user_model()


class AppointmentTestCase(TestCase):
    def setUp(self):
        # Create users
        self.student = User.objects.create_user(
            username='student01',
            email='student01@test.com',
            password='testpass123',
            role='student',
            student_number='STU001'
        )
        
        self.nurse = User.objects.create_user(
            username='nurse01',
            email='nurse01@test.com',
            password='testpass123',
            role='nurse',
            employee_id='NURSE001'
        )
        
        # Create availability
        Availability.objects.create(
            staff=self.nurse,
            day_of_week=1,  # Monday
            start_time='09:00',
            end_time='17:00'
        )
    
    def test_appointment_booking(self):
        """Test appointment booking process"""
        client = Client()
        client.login(username='student01', password='testpass123')
        
        # Test booking page access
        response = client.get(reverse('appointments:appointment_book'))
        self.assertEqual(response.status_code, 200)
        
        # Test appointment creation
        future_date = timezone.now().date() + timedelta(days=7)
        appointment_data = {
            'provider_type': 'nurse',
            'staff': self.nurse.id,
            'appointment_date': future_date,
            'appointment_time': '10:00',
            'reason': 'General checkup'
        }
        
        response = client.post(reverse('appointments:appointment_book'), appointment_data)
        self.assertEqual(Appointment.objects.count(), 1)
        
        appointment = Appointment.objects.first()
        self.assertEqual(appointment.student, self.student)
        self.assertEqual(appointment.staff, self.nurse)
        self.assertEqual(appointment.status, 'pending')
    
    def test_double_booking_prevention(self):
        """Test that double booking is prevented"""
        client = Client()
        client.login(username='student01', password='testpass123')
        
        # Create first appointment
        future_date = timezone.now().date() + timedelta(days=7)
        Appointment.objects.create(
            student=self.student,
            staff=self.nurse,
            provider_type='nurse',
            appointment_date=future_date,
            appointment_time='10:00',
            reason='First appointment',
            status='confirmed'
        )
        
        # Try to create second appointment at same time
        appointment_data = {
            'provider_type': 'nurse',
            'staff': self.nurse.id,
            'appointment_date': future_date,
            'appointment_time': '10:00',
            'reason': 'Second appointment'
        }
        
        response = client.post(reverse('appointments:appointment_book'), appointment_data)
        # Should still only have one appointment
        self.assertEqual(Appointment.objects.count(), 1)
    
    def test_role_based_access(self):
        """Test role-based access control"""
        client = Client()
        
        # Test student cannot access admin pages
        client.login(username='student01', password='testpass123')
        response = client.get(reverse('reports:reports'))
        self.assertEqual(response.status_code, 302)  # Redirect to login/dashboard
        
        # Test staff can access appointment management
        client.login(username='nurse01', password='testpass123')
        response = client.get(reverse('appointments:appointment_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_appointment_cancellation(self):
        """Test appointment cancellation"""
        client = Client()
        client.login(username='student01', password='testpass123')
        
        # Create appointment
        future_date = timezone.now().date() + timedelta(days=7)
        appointment = Appointment.objects.create(
            student=self.student,
            staff=self.nurse,
            provider_type='nurse',
            appointment_date=future_date,
            appointment_time='10:00',
            reason='Test appointment',
            status='confirmed'
        )
        
        # Test cancellation
        response = client.post(reverse('appointments:appointment_cancel', args=[appointment.id]))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'cancelled')
        
        # Check history was created
        self.assertTrue(AppointmentHistory.objects.filter(
            appointment=appointment,
            action='cancelled'
        ).exists())
    
    def test_auto_no_show_logic(self):
        """Test automatic no-show marking logic"""
        # Create past appointment
        past_date = timezone.now().date() - timedelta(days=1)
        appointment = Appointment.objects.create(
            student=self.student,
            staff=self.nurse,
            provider_type='nurse',
            appointment_date=past_date,
            appointment_time='10:00',
            reason='Past appointment',
            status='confirmed'
        )
        
        # Test is_past method
        self.assertTrue(appointment.is_past())
        self.assertFalse(appointment.is_upcoming())
        
        # Test can_be_cancelled
        self.assertFalse(appointment.can_be_cancelled())
        self.assertFalse(appointment.can_be_rescheduled())
        
        # Test mark_as_no_show
        appointment.mark_as_no_show()
        self.assertEqual(appointment.status, 'no_show')


class UserAuthenticationTestCase(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='student01',
            email='student01@test.com',
            password='testpass123',
            role='student',
            student_number='STU001'
        )
    
    def test_user_login(self):
        """Test user login functionality"""
        client = Client()
        
        # Test successful login
        response = client.post(reverse('accounts:login'), {
            'username': 'student01',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        
        # Test login with student number
        client.logout()
        response = client.post(reverse('accounts:login'), {
            'username': 'STU001',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        
        # Test failed login
        client.logout()
        response = client.post(reverse('accounts:login'), {
            'username': 'student01',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')
    
    def test_account_lockout(self):
        """Test account lockout after failed attempts"""
        client = Client()
        
        # Make 5 failed login attempts
        for i in range(5):
            response = client.post(reverse('accounts:login'), {
                'username': 'student01',
                'password': 'wrongpassword'
            })
        
        # Check if account is locked
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_locked)
        
        # Try to login with correct password
        response = client.post(reverse('accounts:login'), {
            'username': 'student01',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your account is locked')
