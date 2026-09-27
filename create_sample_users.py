import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ccams.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.availability.models import Availability
from datetime import time

User = get_user_model()

# 1. Ensure Admin User
admin_user = User.objects.filter(username='admin').first()
if not admin_user:
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@clinic.com',
        first_name='System',
        last_name='Administrator',
        role='admin',
        employee_id='ADMIN001',
        password='admin123'
    )
    print('Created admin user: admin')
else:
    admin_user.set_password('admin123')
    admin_user.role = 'admin'
    admin_user.is_active = True
    admin_user.save()
    print('Updated admin user password to admin123')

# 2. Ensure Student Users
students = [
    {'username': 'student01', 'email': 'student01@university.ac.za', 'first_name': 'James', 'last_name': 'Moyo', 'student_number': 'STU2023001', 'password': 'student123'},
    {'username': 'student02', 'email': 'student02@university.ac.za', 'first_name': 'Ayanda', 'last_name': 'Dlamini', 'student_number': 'STU2023002', 'password': 'student123'},
    {'username': 'student03', 'email': 'student03@university.ac.za', 'first_name': 'Thabo', 'last_name': 'Molefe', 'student_number': 'STU2023003', 'password': 'student123'},
]

for s_data in students:
    s_user = User.objects.filter(username=s_data['username']).first()
    if not s_user:
        s_user = User.objects.create_user(
            username=s_data['username'],
            email=s_data['email'],
            first_name=s_data['first_name'],
            last_name=s_data['last_name'],
            role='student',
            student_number=s_data['student_number'],
            password=s_data['password']
        )
        print(f'Created student: {s_data["username"]}')
    else:
        s_user.set_password(s_data['password'])
        s_user.is_active = True
        s_user.role = 'student'
        s_user.save()
        print(f'Updated student {s_data["username"]} password')

# 3. Create sample nurses
nurses = [
    {'username': 'nurse01', 'email': 'nurse01@clinic.com', 'first_name': 'Sarah', 'last_name': 'Johnson', 'employee_id': 'EMP001', 'phone_number': '555-0101', 'password': 'nurse123'},
    {'username': 'nurse02', 'email': 'nurse02@clinic.com', 'first_name': 'Emily', 'last_name': 'Smith', 'employee_id': 'EMP002', 'phone_number': '555-0102', 'password': 'nurse123'}
]

# 4. Create sample psychologists
psychologists = [
    {'username': 'psych01', 'email': 'psych01@clinic.com', 'first_name': 'Dr. Michael', 'last_name': 'Williams', 'employee_id': 'EMP003', 'phone_number': '555-0103', 'password': 'psych123'},
    {'username': 'psych02', 'email': 'psych02@clinic.com', 'first_name': 'Dr. Jennifer', 'last_name': 'Brown', 'employee_id': 'EMP004', 'phone_number': '555-0104', 'password': 'psych123'}
]

# Create nurses
for nurse_data in nurses:
    n_user = User.objects.filter(username=nurse_data['username']).first()
    if not n_user:
        n_user = User.objects.create_user(
            username=nurse_data['username'],
            email=nurse_data['email'],
            first_name=nurse_data['first_name'],
            last_name=nurse_data['last_name'],
            role='nurse',
            employee_id=nurse_data['employee_id'],
            phone_number=nurse_data['phone_number'],
            password=nurse_data['password']
        )
        print(f'Created nurse: {nurse_data["username"]}')
    else:
        n_user.set_password(nurse_data['password'])
        n_user.is_active = True
        n_user.role = 'nurse'
        n_user.save()
        print(f'Updated nurse {nurse_data["username"]} password')

# Create psychologists
for psych_data in psychologists:
    p_user = User.objects.filter(username=psych_data['username']).first()
    if not p_user:
        p_user = User.objects.create_user(
            username=psych_data['username'],
            email=psych_data['email'],
            first_name=psych_data['first_name'],
            last_name=psych_data['last_name'],
            role='psychologist',
            employee_id=psych_data['employee_id'],
            phone_number=psych_data['phone_number'],
            password=psych_data['password']
        )
        print(f'Created psychologist: {psych_data["username"]}')
    else:
        p_user.set_password(psych_data['password'])
        p_user.is_active = True
        p_user.role = 'psychologist'
        p_user.save()
        print(f'Updated psychologist {psych_data["username"]} password')

# 5. Populate Weekly Availability Schedules for all clinic staff
active_staff = User.objects.filter(role__in=['nurse', 'psychologist'], is_active=True)
slots_created = 0

for staff_member in active_staff:
    for day in range(1, 6):  # Monday (1) to Friday (5)
        # Morning session 08:30 - 12:30
        if not Availability.objects.filter(staff=staff_member, day_of_week=day, start_time=time(8, 30), end_time=time(12, 30)).exists():
            Availability.objects.create(
                staff=staff_member,
                day_of_week=day,
                start_time=time(8, 30),
                end_time=time(12, 30),
                is_active=True
            )
            slots_created += 1
        
        # Afternoon session 13:30 - 16:30
        if not Availability.objects.filter(staff=staff_member, day_of_week=day, start_time=time(13, 30), end_time=time(16, 30)).exists():
            Availability.objects.create(
                staff=staff_member,
                day_of_week=day,
                start_time=time(13, 30),
                end_time=time(16, 30),
                is_active=True
            )
            slots_created += 1

print(f'Created {slots_created} standard weekly availability schedules across clinic staff!')
print('Sample users and clinic schedules ready.')
