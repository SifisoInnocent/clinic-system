# Generated manually for session length and buffer time

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('availability', '0002_alter_availability_staff'),
    ]

    operations = [
        migrations.AddField(
            model_name='availability',
            name='session_length',
            field=models.IntegerField(default=60, help_text='Session length in minutes'),
        ),
        migrations.AddField(
            model_name='availability',
            name='buffer_time',
            field=models.IntegerField(default=15, help_text='Buffer time between sessions in minutes'),
        ),
    ]
