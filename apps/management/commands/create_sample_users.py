from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample users for testing'

    def handle(self, *args, **options):
        # Create sample nurses
        nurses = [
            {
                'username': 'nurse01',
                'email': 'nurse01@clinic.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'employee_id': 'EMP001',
                'phone_number': '555-0101',
                'password': 'nurse123'
            },
            {
                'username': 'nurse02',
                'email': 'nurse02@clinic.com',
                'first_name': 'Emily',
                'last_name': 'Smith',
                'employee_id': 'EMP002',
                'phone_number': '555-0102',
                'password': 'nurse123'
            }
        ]

        # Create sample psychologists
        psychologists = [
            {
                'username': 'psych01',
                'email': 'psych01@clinic.com',
                'first_name': 'Dr. Michael',
                'last_name': 'Williams',
                'employee_id': 'EMP003',
                'phone_number': '555-0103',
                'password': 'psych123'
            },
            {
                'username': 'psych02',
                'email': 'psych02@clinic.com',
                'first_name': 'Dr. Jennifer',
                'last_name': 'Brown',
                'employee_id': 'EMP004',
                'phone_number': '555-0104',
                'password': 'psych123'
            }
        ]

        # Create nurses
        for nurse_data in nurses:
            if not User.objects.filter(username=nurse_data['username']).exists():
                user = User.objects.create_user(
                    username=nurse_data['username'],
                    email=nurse_data['email'],
                    first_name=nurse_data['first_name'],
                    last_name=nurse_data['last_name'],
                    role='nurse',
                    employee_id=nurse_data['employee_id'],
                    phone_number=nurse_data['phone_number'],
                    password=nurse_data['password']
                )
                UserProfile.objects.create(user=user)
                self.stdout.write(self.style.SUCCESS(f"Created nurse: {nurse_data['username']}"))
            else:
                self.stdout.write(self.style.WARNING(f"Nurse {nurse_data['username']} already exists"))

        # Create psychologists
        for psych_data in psychologists:
            if not User.objects.filter(username=psych_data['username']).exists():
                user = User.objects.create_user(
                    username=psych_data['username'],
                    email=psych_data['email'],
                    first_name=psych_data['first_name'],
                    last_name=psych_data['last_name'],
                    role='psychologist',
                    employee_id=psych_data['employee_id'],
                    phone_number=psych_data['phone_number'],
                    password=psych_data['password']
                )
                UserProfile.objects.create(user=user)
                self.stdout.write(self.style.SUCCESS(f"Created psychologist: {psych_data['username']}"))
            else:
                self.stdout.write(self.style.WARNING(f"Psychologist {psych_data['username']} already exists"))

        self.stdout.write(self.style.SUCCESS('Sample users created successfully!'))
