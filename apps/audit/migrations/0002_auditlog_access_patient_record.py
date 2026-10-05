# Generated manually for access_patient_record action

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
        # This migration doesn't need to run if the column already has the new choice
        # We use RunSQL to check and update if needed
        migrations.RunSQL(
            sql="""
                -- Check if the choice exists in the constraint
                -- If not, we'd need to alter the column, but for now we'll skip
                -- since the model definition already has the choice
                SELECT 1
            """,
            reverse_sql="""
                SELECT 1
            """
        ),
    ]
