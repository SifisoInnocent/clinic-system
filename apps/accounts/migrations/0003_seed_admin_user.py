from django.contrib.auth.hashers import make_password
from django.db import migrations

ADMIN_USERNAME = 'SPUAdmin'
ADMIN_PASSWORD = 'Spu@Admin'


def seed_admin_user(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')

    admin, _ = User.objects.get_or_create(username=ADMIN_USERNAME)
    admin.email = 'admin@spuclinic.ac.za'
    admin.first_name = 'System'
    admin.last_name = 'Administrator'
    admin.role = 'admin'
    if not User.objects.filter(employee_id='SPUADMIN001').exclude(pk=admin.pk).exists():
        admin.employee_id = 'SPUADMIN001'
    admin.is_staff = True
    admin.is_superuser = True
    admin.is_active = True
    admin.is_locked = False
    admin.failed_login_attempts = 0
    admin.locked_until = None
    admin.password = make_password(ADMIN_PASSWORD)
    admin.save()

    UserProfile.objects.get_or_create(user=admin)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_create_admin_user'),
    ]

    operations = [
        migrations.RunPython(seed_admin_user, migrations.RunPython.noop),
    ]
