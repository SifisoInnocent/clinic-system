from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

from apps.accounts.models import UserProfile
from apps.availability.models import Availability, BlockedPeriod
from apps.appointments.models import Appointment, AppointmentHistory
from apps.notifications.models import NotificationTemplate

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed initial data for the CCAMS system'
    
    def handle(self, *args, **options):
        """Create initial users, availability, and sample data"""
        
        self.stdout.write('Creating initial data...')
        
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_user(
                username='admin',
                email='admin@clinic.edu',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                role='admin',
                employee_id='ADMIN001',
                is_staff=True,
                is_superuser=True
            )
            UserProfile.objects.create(user=admin)
            self.stdout.write(self.style.SUCCESS('Created admin user: admin/admin123'))
        
        # Create staff users
        if not User.objects.filter(username='nurse01').exists():
            nurse = User.objects.create_user(
                username='nurse01',
                email='nurse01@clinic.edu',
                password='nurse123',
                first_name='Sarah',
                last_name='Johnson',
                role='nurse',
                employee_id='NURSE001',
                phone_number='+263771234567'
            )
            UserProfile.objects.create(user=nurse)
            self.stdout.write(self.style.SUCCESS('Created nurse user: nurse01/nurse123'))
        
        if not User.objects.filter(username='psych01').exists():
            psychologist = User.objects.create_user(
                username='psych01',
                email='psych01@clinic.edu',
                password='psych123',
                first_name='Dr. Michael',
                last_name='Chen',
                role='psychologist',
                employee_id='PSYCH001',
                phone_number='+263772345678'
            )
            UserProfile.objects.create(user=psychologist)
            self.stdout.write(self.style.SUCCESS('Created psychologist user: psych01/psych123'))
        
        # Create student users
        students_data = [
            {
                'username': 'student01',
                'email': 'student01@university.edu',
                'password': 'student123',
                'first_name': 'James',
                'last_name': 'Moyo',
                'student_number': 'STU2023001',
                'phone_number': '+263773456789'
            },
            {
                'username': 'student02',
                'email': 'student02@university.edu',
                'password': 'student123',
                'first_name': 'Grace',
                'last_name': 'Khumalo',
                'student_number': 'STU2023002',
                'phone_number': '+263774567890'
            },
            {
                'username': 'student03',
                'email': 'student03@university.edu',
                'password': 'student123',
                'first_name': 'Tendai',
                'last_name': 'Matsva',
                'student_number': 'STU2023003',
                'phone_number': '+263775678901'
            }
        ]
        
        for student_data in students_data:
            if not User.objects.filter(username=student_data['username']).exists():
                student = User.objects.create_user(
                    username=student_data['username'],
                    email=student_data['email'],
                    password=student_data['password'],
                    first_name=student_data['first_name'],
                    last_name=student_data['last_name'],
                    role='student',
                    student_number=student_data['student_number'],
                    phone_number=student_data['phone_number']
                )
                UserProfile.objects.create(user=student)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created student user: {student_data['username']}/student123"
                    )
                )
        
        # Get created users
        nurse = User.objects.get(username='nurse01')
        psychologist = User.objects.get(username='psych01')
        
        # Create availability for staff
        # Nurse availability (Monday-Friday 8AM-4PM)
        for day in range(1, 6):  # Monday to Friday
            Availability.objects.get_or_create(
                staff=nurse,
                day_of_week=day,
                start_time='08:00',
                end_time='16:00',
                defaults={'is_active': True}
            )
        
        # Psychologist availability (Monday-Friday 9AM-5PM)
        for day in range(1, 6):  # Monday to Friday
            Availability.objects.get_or_create(
                staff=psychologist,
                day_of_week=day,
                start_time='09:00',
                end_time='17:00',
                defaults={'is_active': True}
            )
        
        self.stdout.write(self.style.SUCCESS('Created staff availability'))
        
        # Create sample appointments
        students = User.objects.filter(role='student')
        
        # Past appointments
        past_date = timezone.now().date() - timedelta(days=2)
        Appointment.objects.get_or_create(
            student=students[0],
            staff=nurse,
            provider_type='nurse',
            appointment_date=past_date,
            appointment_time='10:00',
            reason='General checkup and flu symptoms',
            status='completed',
            defaults={'notes': 'Patient recovered well, prescribed medication'}
        )
        
        Appointment.objects.get_or_create(
            student=students[1],
            staff=psychologist,
            provider_type='psychologist',
            appointment_date=past_date,
            appointment_time='14:00',
            reason='Counseling session for anxiety',
            status='completed',
            defaults={'notes': 'Regular counseling session, patient showing improvement'}
        )
        
        # Yesterday's appointments (some no-show)
        yesterday = timezone.now().date() - timedelta(days=1)
        Appointment.objects.get_or_create(
            student=students[2],
            staff=nurse,
            provider_type='nurse',
            appointment_date=yesterday,
            appointment_time='11:00',
            reason='Headache and dizziness',
            status='no_show',
            defaults={'notes': 'Patient did not show up for appointment'}
        )
        
        # Upcoming appointments
        tomorrow = timezone.now().date() + timedelta(days=1)
        Appointment.objects.get_or_create(
            student=students[0],
            staff=psychologist,
            provider_type='psychologist',
            appointment_date=tomorrow,
            appointment_time='10:30',
            reason='Follow-up counseling session',
            status='confirmed',
            defaults={'notification_sent': True}
        )
        
        next_week = timezone.now().date() + timedelta(days=7)
        Appointment.objects.get_or_create(
            student=students[1],
            staff=nurse,
            provider_type='nurse',
            appointment_date=next_week,
            appointment_time='09:00',
            reason='Routine medical examination',
            status='pending',
            defaults={'notification_sent': False}
        )
        
        self.stdout.write(self.style.SUCCESS('Created sample appointments'))
        
        # Create notification templates
        templates_data = [
            {
                'type': 'email',
                'purpose': 'booking',
                'subject_template': 'Appointment Booking Confirmation - {{ appointment.appointment_id }}',
                'message_template': '''
Dear {{ student.get_full_name }},

Your appointment has been successfully booked:

Appointment ID: {{ appointment.appointment_id }}
Date: {{ appointment.appointment_date }}
Time: {{ appointment.appointment_time }}
Provider: {{ staff.get_full_name }} ({{ staff.get_role_display }})
Reason: {{ appointment.reason }}

Please arrive 10 minutes before your scheduled time.

Best regards,
Campus Clinic
                '''.strip()
            },
            {
                'type': 'email',
                'purpose': 'reminder',
                'subject_template': 'Appointment Reminder - {{ appointment.appointment_date }}',
                'message_template': '''
Dear {{ student.get_full_name }},

This is a reminder for your appointment tomorrow:

Appointment ID: {{ appointment.appointment_id }}
Date: {{ appointment.appointment_date }}
Time: {{ appointment.appointment_time }}
Provider: {{ staff.get_full_name }}

Please arrive 10 minutes before your scheduled time.

Best regards,
Campus Clinic
                '''.strip()
            },
            {
                'type': 'sms',
                'purpose': 'booking',
                'message_template': 'Campus Clinic: Appointment confirmed for {{ appointment.appointment_date }} at {{ appointment.appointment_time }} with {{ staff.get_full_name }}. ID: {{ appointment.appointment_id }}'
            },
            {
                'type': 'sms',
                'purpose': 'reminder',
                'message_template': 'Campus Clinic: Reminder - Appointment tomorrow at {{ appointment.appointment_time }} with {{ staff.get_full_name }}. ID: {{ appointment.appointment_id }}'
            }
        ]
        
        for template_data in templates_data:
            NotificationTemplate.objects.get_or_create(
                type=template_data['type'],
                purpose=template_data['purpose'],
                defaults={
                    'subject_template': template_data.get('subject_template', ''),
                    'message_template': template_data['message_template']
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Created notification templates'))
        
        self.stdout.write(
            self.style.SUCCESS('Initial data seeding completed successfully!')
        )
        
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('Admin: admin/admin123')
        self.stdout.write('Nurse: nurse01/nurse123')
        self.stdout.write('Psychologist: psych01/psych123')
        self.stdout.write('Students: student01/student123, student02/student123, student03/student123')
