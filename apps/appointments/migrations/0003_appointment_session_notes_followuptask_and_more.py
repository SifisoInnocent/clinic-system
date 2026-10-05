# Generated manually for session notes and follow-up tasks

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('appointments', '0002_alter_appointment_staff_alter_appointment_student'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='session_notes',
            field=models.TextField(blank=True, help_text='Confidential notes for psychologists'),
        ),
        # Only create FollowUpTask table if it doesn't exist
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS follow_up_tasks (
                    id SERIAL PRIMARY KEY,
                    appointment_id INTEGER NOT NULL,
                    assigned_to_id INTEGER NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    due_date DATE NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id),
                    FOREIGN KEY (assigned_to_id) REFERENCES auth_user(id)
                )
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS follow_up_tasks
            """
        ),
        # Only create AppointmentHistory table if it doesn't exist
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS appointment_history (
                    id SERIAL PRIMARY KEY,
                    appointment_id INTEGER NOT NULL,
                    action VARCHAR(50),
                    old_status VARCHAR(20),
                    new_status VARCHAR(20),
                    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                    notes TEXT,
                    changed_by_id INTEGER,
                    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id),
                    FOREIGN KEY (changed_by_id) REFERENCES auth_user(id)
                )
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS appointment_history
            """
        ),
    ]
