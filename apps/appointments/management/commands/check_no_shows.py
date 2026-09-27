from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from apps.appointments.models import Appointment, AppointmentHistory
from apps.notifications.services import NotificationService
from apps.audit.models import AuditLog


class Command(BaseCommand):
    help = 'Check for appointments that should be marked as no-show'
    
    def handle(self, *args, **options):
        """Check for appointments that are more than 15 minutes past their scheduled time"""
        
        now = timezone.now()
        grace_period = timedelta(minutes=settings.NOSHOW_GRACE_MINUTES)
        
        # Find appointments that should be marked as no-show
        cutoff_time = now - grace_period
        
        appointments_to_check = Appointment.objects.filter(
            status='confirmed',
            appointment_date__lte=now.date()
        ).exclude(
            appointment_date__gt=now.date()
        )
        
        # Filter by time for today's appointments
        appointments_to_mark = []
        
        for appointment in appointments_to_check:
            appointment_datetime = timezone.make_aware(
                timezone.datetime.combine(appointment.appointment_date, appointment.appointment_time)
            )
            
            if appointment_datetime < cutoff_time:
                appointments_to_mark.append(appointment)
        
        # Mark appointments as no-show
        marked_count = 0
        notification_service = NotificationService()
        
        for appointment in appointments_to_mark:
            # Update appointment status
            appointment.status = 'no_show'
            appointment.save()
            
            # Create appointment history
            AppointmentHistory.objects.create(
                appointment=appointment,
                action='marked_no_show',
                old_status='confirmed',
                new_status='no_show',
                changed_by=None,  # System action
                notes='Automatically marked as no-show'
            )
            
            # Log the action
            AuditLog.log_action(
                admin=None,
                action='mark_no_show',
                target_object=f'Appointment {appointment.appointment_id}',
                description=f"Appointment {appointment.appointment_id} automatically marked as no-show",
                ip_address='System',
                user_agent='Django Management Command'
            )
            
            # Send no-show notification
            notification_service.send_no_show_notice(appointment)
            
            marked_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Marked appointment {appointment.appointment_id} as no-show '
                    f'(Student: {appointment.student.get_full_name()}, '
                    f'Staff: {appointment.staff.get_full_name()})'
                )
            )
        
        if marked_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No appointments needed to be marked as no-show.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully marked {marked_count} appointment(s) as no-show.'
                )
            )
