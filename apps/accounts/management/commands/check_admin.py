from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Check admin account status'
    
    def handle(self, *args, **options):
        try:
            admin = User.objects.get(username='admin')
            self.stdout.write(f'Username: {admin.username}')
            self.stdout.write(f'Email: {admin.email}')
            self.stdout.write(f'Role: {admin.role}')
            self.stdout.write(f'Is Active: {admin.is_active}')
            self.stdout.write(f'Is Staff: {admin.is_staff}')
            self.stdout.write(f'Is Superuser: {admin.is_superuser}')
            self.stdout.write(f'Is Locked: {admin.is_locked}')
            self.stdout.write(f'Failed Login Attempts: {admin.failed_login_attempts}')
            self.stdout.write(f'Locked Until: {admin.locked_until}')
            self.stdout.write(f'Can Login: {admin.can_login()}')
            
            # Test password
            if admin.check_password('admin123'):
                self.stdout.write(self.style.SUCCESS('Password "admin123" is correct'))
            else:
                self.stdout.write(self.style.ERROR('Password "admin123" is incorrect'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin user does not exist'))
