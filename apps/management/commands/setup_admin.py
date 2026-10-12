from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or reset the admin portal user on every deploy'

    def handle(self, *args, **options):
        username = 'AdminSpuClinic'
        password = 'SpuClinic@2026'
        email    = 'admin@spuclinic.ac.za'

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email':        email,
                'first_name':   'System',
                'last_name':    'Administrator',
                'role':         'admin',
                'employee_id':  'ADMINSPU001',
                'is_staff':     True,
                'is_superuser': True,
                'is_active':    True,
                'is_locked':    False,
                'failed_login_attempts': 0,
            }
        )

        # Always reset password and ensure correct flags
        user.set_password(password)
        user.role         = 'admin'
        user.is_staff     = True
        user.is_superuser = True
        user.is_active    = True
        user.is_locked    = False
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save()

        # Ensure profile exists
        UserProfile.objects.get_or_create(user=user)

        action = 'Created' if created else 'Reset'
        self.stdout.write(self.style.SUCCESS(
            f'{action} admin: {username} | password: {password}'
        ))
