from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile

User = get_user_model()

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'
ADMIN_EMAIL    = 'admin@clinic.edu'
ADMIN_EMP_ID   = 'ADMIN001'


class Command(BaseCommand):
    help = 'Create or reset the admin account on every deploy'

    def handle(self, *args, **options):
        try:
            # Step 1: Get or create the admin user
            user, created = User.objects.get_or_create(username=ADMIN_USERNAME)

            # Step 2: Force all fields to correct state
            user.email        = ADMIN_EMAIL
            user.first_name   = 'System'
            user.last_name    = 'Administrator'
            user.role         = 'admin'
            user.employee_id  = ADMIN_EMP_ID
            user.is_staff     = True
            user.is_superuser = True
            user.is_active    = True
            user.is_locked    = False
            user.failed_login_attempts = 0
            user.locked_until = None
            user.set_password(ADMIN_PASSWORD)
            user.save()

            # Step 3: Ensure profile exists
            UserProfile.objects.get_or_create(user=user)

            label = 'CREATED' if created else 'RESET'
            self.stdout.write(self.style.SUCCESS(f'[{label}] Admin account ready'))
            self.stdout.write(f'  Username : {ADMIN_USERNAME}')
            self.stdout.write(f'  Password : {ADMIN_PASSWORD}')
            self.stdout.write(self.style.SUCCESS('  Status   : Active, unlocked'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] reset_admin failed: {e}'))
            # Last-resort fallback: force via raw SQL
            from django.db import connection
            self.stdout.write('  Attempting raw SQL fallback...')
            try:
                from django.contrib.auth.hashers import make_password
                hashed = make_password(ADMIN_PASSWORD)
                with connection.cursor() as cur:
                    cur.execute(
                        "UPDATE auth_user SET password=%s, is_active=1, is_locked=0, "
                        "failed_login_attempts=0 WHERE username=%s",
                        [hashed, ADMIN_USERNAME]
                    )
                    if cur.rowcount == 0:
                        self.stdout.write(self.style.WARNING('  User not found via SQL either.'))
                    else:
                        self.stdout.write(self.style.SUCCESS('  Password reset via SQL fallback.'))
            except Exception as e2:
                self.stdout.write(self.style.ERROR(f'  SQL fallback also failed: {e2}'))
