# Generated manually for session length and buffer time

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('availability', '0002_alter_availability_staff'),
    ]

    operations = [
        # Add session_length column if it doesn't exist
        migrations.RunSQL(
            sql="""
                ALTER TABLE availability
                ADD COLUMN IF NOT EXISTS session_length INTEGER DEFAULT 60
            """,
            reverse_sql="""
                ALTER TABLE availability DROP COLUMN IF EXISTS session_length
            """
        ),
        # Add buffer_time column if it doesn't exist
        migrations.RunSQL(
            sql="""
                ALTER TABLE availability
                ADD COLUMN IF NOT EXISTS buffer_time INTEGER DEFAULT 15
            """,
            reverse_sql="""
                ALTER TABLE availability DROP COLUMN IF EXISTS buffer_time
            """
        ),
    ]
