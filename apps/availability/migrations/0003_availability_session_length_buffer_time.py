# Generated manually for session length and buffer time

from django.db import migrations


class PostgresOnlyRunSQL(migrations.RunSQL):
    """Raw SQL below is PostgreSQL-specific; on other backends 0004 adds these columns."""

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('availability', '0002_alter_availability_staff'),
    ]

    operations = [
        # Add session_length column if it doesn't exist
        PostgresOnlyRunSQL(
            sql="""
                ALTER TABLE availability
                ADD COLUMN IF NOT EXISTS session_length INTEGER DEFAULT 60
            """,
            reverse_sql="""
                ALTER TABLE availability DROP COLUMN IF EXISTS session_length
            """
        ),
        # Add buffer_time column if it doesn't exist
        PostgresOnlyRunSQL(
            sql="""
                ALTER TABLE availability
                ADD COLUMN IF NOT EXISTS buffer_time INTEGER DEFAULT 15
            """,
            reverse_sql="""
                ALTER TABLE availability DROP COLUMN IF EXISTS buffer_time
            """
        ),
    ]
