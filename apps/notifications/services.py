from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import NotificationLog, NotificationTemplate


class NotificationService:
    """Service for sending email and SMS notifications"""
    
    def send_booking_confirmation(self, appointment):
        """Send booking confirmation to student"""
        context = {
            'appointment': appointment,
            'student': appointment.student,
            'staff': appointment.staff,
            'clinic_name': 'Campus Clinic',
        }
        
        # Send email to student
        self._send_email(
            appointment.student.email,
            'appointment_booking',
            context,
            appointment=appointment
        )
        
        # Send SMS if phone number available
        if appointment.student.phone_number:
            self._send_sms(
                appointment.student.phone_number,
                'appointment_booking',
                context,
                appointment=appointment
            )
    
    def send_cancellation_notice(self, appointment):
        """Send cancellation notice"""
        context = {
            'appointment': appointment,
            'student': appointment.student,
            'staff': appointment.staff,
            'clinic_name': 'Campus Clinic',
        }
        
        # Send email to student
        self._send_email(
            appointment.student.email,
            'appointment_cancellation',
            context,
            appointment=appointment
        )
        
        # Send email to staff
        self._send_email(
            appointment.staff.email,
            'staff_cancellation',
            context,
            appointment=appointment
        )
        
        # Send SMS to student if phone number available
        if appointment.student.phone_number:
            self._send_sms(
                appointment.student.phone_number,
                'appointment_cancellation',
                context,
                appointment=appointment
            )
    
    def send_reschedule_confirmation(self, appointment):
        """Send reschedule confirmation"""
        context = {
            'appointment': appointment,
            'student': appointment.student,
            'staff': appointment.staff,
            'clinic_name': 'Campus Clinic',
        }
        
        # Send email to student
        self._send_email(
            appointment.student.email,
            'appointment_reschedule',
            context,
            appointment=appointment
        )
        
        # Send email to staff
        self._send_email(
            appointment.staff.email,
            'staff_reschedule',
            context,
            appointment=appointment
        )
        
        # Send SMS to student if phone number available
        if appointment.student.phone_number:
            self._send_sms(
                appointment.student.phone_number,
                'appointment_reschedule',
                context,
                appointment=appointment
            )
    
    def send_reminder(self, appointment):
        """Send 24-hour reminder"""
        context = {
            'appointment': appointment,
            'student': appointment.student,
            'staff': appointment.staff,
            'clinic_name': 'Campus Clinic',
        }
        
        # Send email to student
        self._send_email(
            appointment.student.email,
            'appointment_reminder',
            context,
            appointment=appointment
        )
        
        # Send SMS if phone number available
        if appointment.student.phone_number:
            self._send_sms(
                appointment.student.phone_number,
                'appointment_reminder',
                context,
                appointment=appointment
            )
        
        # Mark reminder as sent
        appointment.reminder_sent = True
        appointment.save()
    
    def send_completion_notice(self, appointment):
        """Send completion notice"""
        context = {
            'appointment': appointment,
            'student': appointment.student,
            'staff': appointment.staff,
            'clinic_name': 'Campus Clinic',
        }
        
        # Send email to student
        self._send_email(
            appointment.student.email,
            'appointment_completed',
            context,
            appointment=appointment
        )
    
    def send_no_show_notice(self, appointment):
        """Send no-show notice"""
        context = {
            'appointment': appointment,
            'student': appointment.student,
            'staff': appointment.staff,
            'clinic_name': 'Campus Clinic',
        }
        
        # Send email to student
        self._send_email(
            appointment.student.email,
            'appointment_no_show',
            context,
            appointment=appointment
        )
    
    def _send_email(self, recipient, purpose, context, appointment=None):
        """Send email notification"""
        try:
            # Get template
            template = NotificationTemplate.objects.filter(
                type='email',
                purpose=purpose,
                is_active=True
            ).first()
            
            if not template:
                # Use default templates
                subject = self._get_default_email_subject(purpose, context)
                message = self._get_default_email_message(purpose, context)
            else:
                subject = template.render_subject(context)
                message = template.render_message(context)
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            
            # Log successful email
            NotificationLog.objects.create(
                type='email',
                recipient=recipient,
                appointment=appointment,
                purpose=purpose,
                subject=subject,
                message=message,
                status='sent',
                sent_at=timezone.now()
            )
            
        except Exception as e:
            # Log failed email
            NotificationLog.objects.create(
                type='email',
                recipient=recipient,
                appointment=appointment,
                purpose=purpose,
                message=str(e),
                status='failed',
                error_message=str(e)
            )
    
    def _send_sms(self, recipient, purpose, context, appointment=None):
        """Send SMS notification (simulated)"""
        try:
            # Get template
            template = NotificationTemplate.objects.filter(
                type='sms',
                purpose=purpose,
                is_active=True
            ).first()
            
            if not template:
                # Use default SMS templates
                message = self._get_default_sms_message(purpose, context)
            else:
                message = template.render_message(context)
            
            # Simulate SMS sending (in production, integrate with Africa's Talking or Twilio)
            # For now, we'll just log it as sent
            print(f"SMS to {recipient}: {message}")
            
            # Log successful SMS
            NotificationLog.objects.create(
                type='sms',
                recipient=recipient,
                appointment=appointment,
                purpose=purpose,
                message=message,
                status='sent',
                sent_at=timezone.now()
            )
            
        except Exception as e:
            # Log failed SMS
            NotificationLog.objects.create(
                type='sms',
                recipient=recipient,
                appointment=appointment,
                purpose=purpose,
                message=str(e),
                status='failed',
                error_message=str(e)
            )
    
    def _get_default_email_subject(self, purpose, context):
        """Get default email subject"""
        subjects = {
            'appointment_booking': 'Appointment Booking Confirmation',
            'appointment_cancellation': 'Appointment Cancellation Notice',
            'appointment_reschedule': 'Appointment Reschedule Confirmation',
            'appointment_reminder': 'Appointment Reminder',
            'appointment_completed': 'Appointment Completion Notice',
            'appointment_no_show': 'Appointment No-Show Notice',
            'staff_cancellation': 'Appointment Cancellation Notice',
            'staff_reschedule': 'Appointment Reschedule Notice',
        }
        return subjects.get(purpose, 'Campus Clinic Notification')
    
    def _get_default_email_message(self, purpose, context):
        """Get default email message"""
        appointment = context.get('appointment')
        student = context.get('student')
        staff = context.get('staff')
        
        if purpose == 'appointment_booking':
            return f"""
Dear {student.get_full_name()},

Your appointment has been successfully booked:

Appointment ID: {appointment.appointment_id}
Date: {appointment.appointment_date}
Time: {appointment.appointment_time}
Provider: {staff.get_full_name()} ({staff.get_role_display()})
Reason: {appointment.reason}

Please arrive 10 minutes before your scheduled time.

Best regards,
Campus Clinic
"""
        elif purpose == 'appointment_cancellation':
            return f"""
Dear {student.get_full_name()},

Your appointment has been cancelled:

Appointment ID: {appointment.appointment_id}
Date: {appointment.appointment_date}
Time: {appointment.appointment_time}
Provider: {staff.get_full_name()}

If you need to reschedule, please book a new appointment through the system.

Best regards,
Campus Clinic
"""
        elif purpose == 'appointment_reminder':
            return f"""
Dear {student.get_full_name()},

This is a reminder for your appointment tomorrow:

Appointment ID: {appointment.appointment_id}
Date: {appointment.appointment_date}
Time: {appointment.appointment_time}
Provider: {staff.get_full_name()}

Please arrive 10 minutes before your scheduled time.

Best regards,
Campus Clinic
"""
        
        return "This is a notification from Campus Clinic."
    
    def _get_default_sms_message(self, purpose, context):
        """Get default SMS message"""
        appointment = context.get('appointment')
        staff = context.get('staff')
        
        if purpose == 'appointment_booking':
            return f"Campus Clinic: Appointment confirmed for {appointment.appointment_date} at {appointment.appointment_time} with {staff.get_full_name()}. ID: {appointment.appointment_id}"
        elif purpose == 'appointment_cancellation':
            return f"Campus Clinic: Appointment {appointment.appointment_id} on {appointment.appointment_date} has been cancelled."
        elif purpose == 'appointment_reminder':
            return f"Campus Clinic: Reminder - Appointment tomorrow at {appointment.appointment_time} with {staff.get_full_name()}. ID: {appointment.appointment_id}"
        
        return "Campus Clinic: You have a notification regarding your appointment."
