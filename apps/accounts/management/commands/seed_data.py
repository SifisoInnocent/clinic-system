from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import connection

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
        
        # Check if new columns exist in database (handle both SQLite and PostgreSQL)
        try:
            with connection.cursor() as cursor:
                # Check database type
                db_vendor = connection.vendor
                
                if db_vendor == 'sqlite':
                    cursor.execute("PRAGMA table_info(availability)")
                    columns = [column[1] for column in cursor.fetchall()]
                    has_session_length = 'session_length' in columns
                    has_buffer_time = 'buffer_time' in columns
                    
                    if not has_session_length:
                        cursor.execute('ALTER TABLE availability ADD COLUMN session_length INTEGER DEFAULT 60')
                        self.stdout.write(self.style.WARNING('Added session_length column to availability'))
                    if not has_buffer_time:
                        cursor.execute('ALTER TABLE availability ADD COLUMN buffer_time INTEGER DEFAULT 15')
                        self.stdout.write(self.style.WARNING('Added buffer_time column to availability'))
                    
                    cursor.execute("PRAGMA table_info(appointments)")
                    columns = [column[1] for column in cursor.fetchall()]
                    has_session_notes = 'session_notes' in columns
                    
                    if not has_session_notes:
                        cursor.execute('ALTER TABLE appointments ADD COLUMN session_notes TEXT')
                        self.stdout.write(self.style.WARNING('Added session_notes column to appointments'))
                    
                    # Check if follow_up_tasks table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='follow_up_tasks'")
                    if not cursor.fetchone():
                        cursor.execute('''
                            CREATE TABLE follow_up_tasks (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                appointment_id INTEGER NOT NULL,
                                assigned_to_id INTEGER NOT NULL,
                                status VARCHAR(20) DEFAULT 'pending',
                                due_date DATE NOT NULL,
                                notes TEXT,
                                created_at DATETIME NOT NULL,
                                updated_at DATETIME NOT NULL,
                                FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id),
                                FOREIGN KEY (assigned_to_id) REFERENCES auth_user(id)
                            )
                        ''')
                        self.stdout.write(self.style.WARNING('Created follow_up_tasks table'))
                elif db_vendor == 'postgresql':
                    # PostgreSQL-specific checks
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'availability' AND column_name = 'session_length'
                    """)
                    has_session_length = cursor.fetchone() is not None
                    
                    if not has_session_length:
                        cursor.execute('ALTER TABLE availability ADD COLUMN session_length INTEGER DEFAULT 60')
                        self.stdout.write(self.style.WARNING('Added session_length column to availability'))
                    
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'availability' AND column_name = 'buffer_time'
                    """)
                    has_buffer_time = cursor.fetchone() is not None
                    
                    if not has_buffer_time:
                        cursor.execute('ALTER TABLE availability ADD COLUMN buffer_time INTEGER DEFAULT 15')
                        self.stdout.write(self.style.WARNING('Added buffer_time column to availability'))
                    
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'appointments' AND column_name = 'session_notes'
                    """)
                    has_session_notes = cursor.fetchone() is not None
                    
                    if not has_session_notes:
                        cursor.execute('ALTER TABLE appointments ADD COLUMN session_notes TEXT')
                        self.stdout.write(self.style.WARNING('Added session_notes column to appointments'))
                    
                    # Check if follow_up_tasks table exists
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_name = 'follow_up_tasks'
                    """)
                    if not cursor.fetchone():
                        cursor.execute('''
                            CREATE TABLE follow_up_tasks (
                                id SERIAL PRIMARY KEY,
                                appointment_id INTEGER NOT NULL,
                                assigned_to_id INTEGER NOT NULL,
                                status VARCHAR(20) DEFAULT 'pending',
                                due_date DATE NOT NULL,
                                notes TEXT,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL,
                                FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id),
                                FOREIGN KEY (assigned_to_id) REFERENCES auth_user(id)
                            )
                        ''')
                        self.stdout.write(self.style.WARNING('Created follow_up_tasks table'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Database schema check skipped: {e}'))
        
        # Create or reset admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@clinic.edu',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'admin',
                'employee_id': 'ADMIN001',
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin.set_password('admin123')
        admin.save()
        
        if created:
            UserProfile.objects.get_or_create(user=admin)
        
        self.stdout.write(self.style.SUCCESS('Admin user ready: admin/admin123'))
        
        # Create staff users
        nurse, created = User.objects.get_or_create(
            username='nurse01',
            defaults={
                'email': 'nurse01@clinic.edu',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'role': 'nurse',
                'employee_id': 'NURSE001',
                'phone_number': '+263771234567'
            }
        )
        nurse.set_password('nurse123')
        nurse.save()
        if created:
            UserProfile.objects.get_or_create(user=nurse)
        self.stdout.write(self.style.SUCCESS('Nurse user ready: nurse01/nurse123'))
        
        psychologist, created = User.objects.get_or_create(
            username='psych01',
            defaults={
                'email': 'psych01@clinic.edu',
                'first_name': 'Dr. Michael',
                'last_name': 'Chen',
                'role': 'psychologist',
                'employee_id': 'PSYCH001',
                'phone_number': '+263772345678'
            }
        )
        psychologist.set_password('psych123')
        psychologist.save()
        if created:
            UserProfile.objects.get_or_create(user=psychologist)
        self.stdout.write(self.style.SUCCESS('Psychologist user ready: psych01/psych123'))
        
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
        try:
            nurse = User.objects.get(username='nurse01')
            psychologist = User.objects.get(username='psych01')
            
            # Create availability for staff (skip if already exists)
            # Nurse availability (Monday-Friday 8AM-4PM)
            for day in range(1, 6):  # Monday to Friday
                try:
                    Availability.objects.get_or_create(
                        staff=nurse,
                        day_of_week=day,
                        start_time='08:00',
                        end_time='16:00',
                        defaults={'is_active': True, 'session_length': 60, 'buffer_time': 15}
                    )
                except Exception:
                    pass  # Skip if already exists or has conflicts
            
            # Psychologist availability (Monday-Friday 9AM-5PM)
            for day in range(1, 6):  # Monday to Friday
                try:
                    Availability.objects.get_or_create(
                        staff=psychologist,
                        day_of_week=day,
                        start_time='09:00',
                        end_time='17:00',
                        defaults={'is_active': True, 'session_length': 60, 'buffer_time': 15}
                    )
                except Exception:
                    pass  # Skip if already exists or has conflicts
            
            self.stdout.write(self.style.SUCCESS('Staff availability ready'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Staff availability skipped: {e}'))
        
        # Create sample appointments (skip if fails)
        try:
            students = User.objects.filter(role='student')
            
            if students.count() >= 3:
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
                
                self.stdout.write(self.style.SUCCESS('Sample appointments ready'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Sample appointments skipped: {e}'))
        
        # Create notification templates (skip if fails)
        try:
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
            
            self.stdout.write(self.style.SUCCESS('Notification templates ready'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Notification templates skipped: {e}'))
        
        self.stdout.write(
            self.style.SUCCESS('Initial data seeding completed successfully!')
        )
        
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('Admin: admin/admin123')
        self.stdout.write('Nurse: nurse01/nurse123')
        self.stdout.write('Psychologist: psych01/psych123')
        self.stdout.write('Students: student01/student123, student02/student123, student03/student123')
