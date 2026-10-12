from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile

User = get_user_model()

ADMIN_USERNAME = 'AdminSpuClinic'
ADMIN_PASSWORD = 'SpuClinic@2026'
ADMIN_EMAIL    = 'admin@spuclinic.ac.za'


class Command(BaseCommand):
    help = 'Create or reset the AdminSpuClinic admin account on every deploy'

    def handle(self, *args, **options):
        # Remove any old default 'admin' user if it still exists
        User.objects.filter(username='admin', role='admin').delete()

        # Create or update the real admin account
        user, created = User.objects.get_or_create(
            username=ADMIN_USERNAME,
            defaults={
                'email':        ADMIN_EMAIL,
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

        # Always force correct state regardless of create/update
        user.set_password(ADMIN_PASSWORD)
        user.role         = 'admin'
        user.is_staff     = True
        user.is_superuser = True
        user.is_active    = True
        user.is_locked    = False
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save()

        UserProfile.objects.get_or_create(user=user)

        label = 'Created' if created else 'Reset'
        self.stdout.write(self.style.SUCCESS(f'[{label}] Admin account ready'))
        self.stdout.write(f'  Username : {ADMIN_USERNAME}')
        self.stdout.write(f'  Password : {ADMIN_PASSWORD}')
        self.stdout.write(self.style.SUCCESS('  Status   : Active, unlocked'))
