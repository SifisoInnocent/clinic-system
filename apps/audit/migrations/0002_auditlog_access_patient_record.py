# Generated manually for access_patient_record action

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(
                choices=[
                    ('create_user', 'Create User'),
                    ('update_user', 'Update User'),
                    ('deactivate_user', 'Deactivate User'),
                    ('delete_user', 'Delete User'),
                    ('login', 'User Login'),
                    ('logout', 'User Logout'),
                    ('failed_login', 'Failed Login'),
                    ('account_locked', 'Account Locked'),
                    ('account_unlocked', 'Account Unlocked'),
                    ('password_reset', 'Password Reset'),
                    ('create_appointment', 'Create Appointment'),
                    ('update_appointment', 'Update Appointment'),
                    ('cancel_appointment', 'Cancel Appointment'),
                    ('reschedule_appointment', 'Reschedule Appointment'),
                    ('complete_appointment', 'Complete Appointment'),
                    ('mark_no_show', 'Mark No-Show'),
                    ('create_availability', 'Create Availability'),
                    ('update_availability', 'Update Availability'),
                    ('delete_availability', 'Delete Availability'),
                    ('create_blocked_period', 'Create Blocked Period'),
                    ('update_blocked_period', 'Update Blocked Period'),
                    ('delete_blocked_period', 'Delete Blocked Period'),
                    ('generate_report', 'Generate Report'),
                    ('export_data', 'Export Data'),
                    ('system_config', 'System Configuration'),
                    ('access_patient_record', 'Access Patient Record'),
                ],
                max_length=30
            ),
        ),
    ]
