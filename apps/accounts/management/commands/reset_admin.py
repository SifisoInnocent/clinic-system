from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Reset admin password to admin123 or create admin if not exists'
    
    def handle(self, *args, **options):
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
            self.stdout.write(self.style.SUCCESS('Admin user created'))
        else:
            self.stdout.write(self.style.SUCCESS('Admin password reset'))
        
        self.stdout.write('Username: admin')
        self.stdout.write('Password: admin123')
