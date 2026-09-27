from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from .models import Appointment, AppointmentHistory

User = get_user_model()
from .forms import (
    AppointmentBookingForm, AppointmentRescheduleForm, 
    AppointmentStatusUpdateForm, AppointmentSearchForm
)
from apps.accounts.decorators import student_required, staff_required, admin_or_staff_required
from apps.availability.models import Availability
from apps.notifications.services import NotificationService
from apps.audit.models import AuditLog


@login_required
def appointment_list_view(request):
    """List appointments based on user role"""
    user = request.user
    
    if user.is_student():
        appointments = Appointment.objects.filter(student=user).order_by('-appointment_date', '-appointment_time')
    elif user.is_staff_user():
        appointments = Appointment.objects.filter(staff=user).order_by('appointment_date', 'appointment_time')
    else:  # admin
        appointments = Appointment.objects.all().order_by('-appointment_date', '-appointment_time')
    
    # Apply search filters
    form = AppointmentSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if search:
            if user.is_student():
                appointments = appointments.filter(
                    Q(reason__icontains=search) |
                    Q(staff__first_name__icontains=search) |
                    Q(staff__last_name__icontains=search)
                )
            elif user.is_staff_user():
                appointments = appointments.filter(
                    Q(student__first_name__icontains=search) |
                    Q(student__last_name__icontains=search) |
                    Q(student__student_number__icontains=search) |
                    Q(reason__icontains=search)
                )
            else:  # admin
                appointments = appointments.filter(
                    Q(student__first_name__icontains=search) |
                    Q(student__last_name__icontains=search) |
                    Q(student__student_number__icontains=search) |
                    Q(staff__first_name__icontains=search) |
                    Q(staff__last_name__icontains=search) |
                    Q(reason__icontains=search)
                )
        
        if status:
            appointments = appointments.filter(status=status)
        
        if date_from:
            appointments = appointments.filter(appointment_date__gte=date_from)
        
        if date_to:
            appointments = appointments.filter(appointment_date__lte=date_to)
    
    # Pagination
    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'appointments': page_obj,
        'form': form,
        'is_student': user.is_student(),
        'is_staff': user.is_staff_user(),
        'is_admin': user.is_admin(),
    }
    
    return render(request, 'appointments/appointment_list.html', context)


@student_required
def appointment_book_view(request):
    """Book new appointment (student only)"""
    # Load all active nurses and psychologists
    nurses = User.objects.filter(role='nurse', is_active=True).order_by('first_name', 'last_name')
    psychologists = User.objects.filter(role='psychologist', is_active=True).order_by('first_name', 'last_name')
    
    if request.method == 'POST':
        from .forms_simple import SimpleAppointmentBookingForm
        form = SimpleAppointmentBookingForm(request.POST)
        if form.is_valid():
            try:
                # Create appointment manually to avoid model form issues
                appointment = Appointment.objects.create(
                    student=request.user,
                    staff=form.cleaned_data['staff'],
                    provider_type=form.cleaned_data['provider_type'],
                    appointment_date=form.cleaned_data['appointment_date'],
                    appointment_time=form.cleaned_data['appointment_time'],
                    reason=form.cleaned_data['reason'],
                    status='pending'
                )
                
                # Create appointment history
                AppointmentHistory.objects.create(
                    appointment=appointment,
                    action='created',
                    new_status='pending',
                    changed_by=request.user,
                    notes='Appointment created'
                )
                
                # Log appointment creation
                AuditLog.log_action(
                    admin=request.user,
                    action='create_appointment',
                    target_object=f'Appointment {appointment.appointment_id}',
                    description=f"Student {request.user.username} booked appointment with {appointment.staff.get_full_name()}",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Send notification
                notification_service = NotificationService()
                notification_service.send_booking_confirmation(appointment)
                
                messages.success(request, 'Your appointment has been booked successfully! You will receive a confirmation email.')
                return redirect('appointments:appointment_detail', appointment_id=appointment.appointment_id)
            except ValidationError as e:
                for error in getattr(e, 'messages', [str(e)]):
                    form.add_error(None, error)
    else:
        from .forms_simple import SimpleAppointmentBookingForm
        # Handle pre-selection from dashboard
        initial_data = {}
        provider_type = request.GET.get('provider_type')
        staff_id = request.GET.get('staff')
        
        if provider_type:
            initial_data['provider_type'] = provider_type
            if staff_id:
                try:
                    staff = User.objects.get(id=staff_id, role=provider_type, is_active=True)
                    initial_data['staff'] = staff
                except User.DoesNotExist:
                    pass
        
        form = SimpleAppointmentBookingForm(initial=initial_data)
    
    context = {
        'form': form,
        'nurses': nurses,
        'psychologists': psychologists,
        'available_nurses': nurses,
        'available_psychologists': psychologists,
        'today': timezone.now().date(),
    }
    
    return render(request, 'appointments/appointment_book_simple.html', context)


@login_required
def appointment_detail_view(request, appointment_id):
    """View appointment details"""
    user = request.user
    
    if user.is_student():
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id, student=user)
    elif user.is_staff_user():
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id, staff=user)
    else:  # admin
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    
    # Get appointment history
    history = appointment.history.all().order_by('-timestamp')
    
    context = {
        'appointment': appointment,
        'history': history,
        'can_cancel': appointment.can_be_cancelled(),
        'can_reschedule': appointment.can_be_rescheduled(),
        'is_student': user.is_student(),
        'is_staff': user.is_staff_user(),
        'is_admin': user.is_admin(),
    }
    
    return render(request, 'appointments/appointment_detail.html', context)


@login_required
def appointment_slip_view(request, appointment_id):
    """View official printable clinic attendance & verification slip"""
    user = request.user
    
    if user.is_student():
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id, student=user)
    elif user.is_staff_user():
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id, staff=user)
    else:  # admin
        appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
        
    context = {
        'appointment': appointment,
        'today': timezone.now(),
        'is_student': user.is_student(),
        'is_staff': user.is_staff_user(),
        'is_admin': user.is_admin(),
    }
    return render(request, 'appointments/appointment_slip.html', context)


@student_required
def appointment_cancel_view(request, appointment_id):
    """Cancel appointment (student only)"""
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, student=request.user)
    
    if not appointment.can_be_cancelled():
        messages.error(request, 'This appointment cannot be cancelled.')
        return redirect('appointments:appointment_detail', appointment_id=appointment_id)
    
    if request.method == 'POST':
        old_status = appointment.status
        appointment.status = 'cancelled'
        appointment.save()
        
        # Create appointment history
        AppointmentHistory.objects.create(
            appointment=appointment,
            action='cancelled',
            old_status=old_status,
            new_status='cancelled',
            changed_by=request.user,
            notes='Appointment cancelled by student'
        )
        
        # Log cancellation
        AuditLog.log_action(
            admin=request.user,
            action='cancel_appointment',
            target_object=f'Appointment {appointment.appointment_id}',
            description=f"Student {request.user.username} cancelled appointment",
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send notifications
        notification_service = NotificationService()
        notification_service.send_cancellation_notice(appointment)
        
        messages.success(request, 'Your appointment has been cancelled successfully.')
        return redirect('appointments:appointment_list')
    
    return render(request, 'appointments/appointment_cancel.html', {'appointment': appointment})


@student_required
def appointment_reschedule_view(request, appointment_id):
    """Reschedule appointment (student only)"""
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, student=request.user)
    
    if not appointment.can_be_rescheduled():
        messages.error(request, 'This appointment cannot be rescheduled.')
        return redirect('appointments:appointment_detail', appointment_id=appointment_id)
    
    if request.method == 'POST':
        form = AppointmentRescheduleForm(request.POST, appointment=appointment)
        if form.is_valid():
            # Store old values
            old_staff = appointment.staff
            old_date = appointment.appointment_date
            old_time = appointment.appointment_time
            
            # Update appointment
            appointment.staff = form.cleaned_data['staff']
            appointment.appointment_date = form.cleaned_data['appointment_date']
            appointment.appointment_time = form.cleaned_data['appointment_time']
            appointment.status = 'pending'  # Reset to pending
            appointment.save()
            
            # Create appointment history
            AppointmentHistory.objects.create(
                appointment=appointment,
                action='rescheduled',
                old_status='confirmed',
                new_status='pending',
                changed_by=request.user,
                notes=f'Rescheduled from {old_date} {old_time} with {old_staff.get_full_name()} to {appointment.appointment_date} {appointment.appointment_time} with {appointment.staff.get_full_name()}'
            )
            
            # Log reschedule
            AuditLog.log_action(
                admin=request.user,
                action='reschedule_appointment',
                target_object=f'Appointment {appointment.appointment_id}',
                description=f"Student {request.user.username} rescheduled appointment",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send notifications
            notification_service = NotificationService()
            notification_service.send_reschedule_confirmation(appointment)
            
            messages.success(request, 'Your appointment has been rescheduled successfully!')
            return redirect('appointments:appointment_detail', appointment_id=appointment.appointment_id)
    else:
        form = AppointmentRescheduleForm(appointment=appointment)
    
    return render(request, 'appointments/appointment_reschedule.html', {
        'form': form, 
        'appointment': appointment
    })


@staff_required
def appointment_update_status_view(request, appointment_id):
    """Update appointment status (staff only)"""
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, staff=request.user)
    
    if request.method == 'POST':
        form = AppointmentStatusUpdateForm(request.POST, instance=appointment)
        if form.is_valid():
            old_status = appointment.status
            form.save()
            
            # Create appointment history
            AppointmentHistory.objects.create(
                appointment=appointment,
                action='status_updated',
                old_status=old_status,
                new_status=appointment.status,
                changed_by=request.user,
                notes=f'Status updated by {request.user.get_full_name()}'
            )
            
            # Log status update
            action_map = {
                'completed': 'complete_appointment',
                'no_show': 'mark_no_show',
                'cancelled': 'cancel_appointment',
            }
            
            action = action_map.get(appointment.status, 'update_appointment')
            AuditLog.log_action(
                admin=request.user,
                action=action,
                target_object=f'Appointment {appointment.appointment_id}',
                description=f"Staff {request.user.username} updated appointment status to {appointment.status}",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send notifications if completed or no-show
            if appointment.status in ['completed', 'no_show']:
                notification_service = NotificationService()
                if appointment.status == 'completed':
                    notification_service.send_completion_notice(appointment)
                else:
                    notification_service.send_no_show_notice(appointment)
            
            messages.success(request, f'Appointment status updated to {appointment.get_status_display()}.')
            return redirect('appointments:appointment_detail', appointment_id=appointment.appointment_id)
    else:
        form = AppointmentStatusUpdateForm(instance=appointment)
    
    return render(request, 'appointments/appointment_update_status.html', {
        'form': form, 
        'appointment': appointment
    })


@login_required
def get_available_slots_view(request):
    """Get available time slots via AJAX"""
    staff_id = request.GET.get('staff_id')
    date = request.GET.get('date')
    
    if not staff_id or not date:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        from apps.accounts.models import User
        from datetime import datetime, timedelta
        
        staff = User.objects.get(id=staff_id)
        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Check if date is in the past
        if appointment_date < timezone.now().date():
            return JsonResponse({'slots': []})
        
        # Get staff availability for that day
        day_of_week = appointment_date.isoweekday()
        if day_of_week > 5:  # Weekend
            return JsonResponse({'slots': []})
        
        availabilities = Availability.objects.filter(
            staff=staff,
            day_of_week=day_of_week,
            is_active=True
        )
        
        # Generate time slots
        available_slots = []
        for availability in availabilities:
            current_time = availability.start_time
            end_time = availability.end_time
            
            while current_time < end_time:
                # Check if slot is not blocked
                slot_datetime = timezone.make_aware(
                    datetime.combine(appointment_date, current_time)
                )
                
                from apps.availability.models import BlockedPeriod
                blocked = BlockedPeriod.objects.filter(
                    staff=staff,
                    start_datetime__lte=slot_datetime,
                    end_datetime__gte=slot_datetime,
                    is_active=True
                ).exists()
                
                if not blocked:
                    # Check if slot is not in the past if booking for today
                    is_past_slot = (appointment_date == timezone.now().date() and current_time <= timezone.localtime().time())
                    
                    if not is_past_slot:
                        # Check if slot is not already booked
                        booked = Appointment.objects.filter(
                            staff=staff,
                            appointment_date=appointment_date,
                            appointment_time=current_time,
                            status__in=['pending', 'confirmed']
                        ).exists()
                        
                        if not booked:
                            available_slots.append({
                                'time': current_time.strftime('%H:%M'),
                                'display': current_time.strftime('%I:%M %p')
                            })
                
                # Increment by 30 minutes
                current_time = (datetime.combine(datetime.min, current_time) + timedelta(minutes=30)).time()
        
        return JsonResponse({'slots': available_slots})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_staff_by_type_view(request):
    """Get staff members by provider type"""
    try:
        provider_type = request.GET.get('provider_type') or request.GET.get('type')
        
        if not provider_type:
            return JsonResponse({'error': 'Provider type is required'}, status=400)
        
        # Get staff based on provider type
        if provider_type == 'nurse':
            staff_users = User.objects.filter(role='nurse', is_active=True)
        elif provider_type == 'psychologist':
            staff_users = User.objects.filter(role='psychologist', is_active=True)
        else:
            return JsonResponse({'error': 'Invalid provider type'}, status=400)
        
        # Format staff data
        staff_data = []
        for user in staff_users:
            staff_data.append({
                'id': user.id,
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'phone': user.phone_number
            })
        
        return JsonResponse({'staff': staff_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def appointment_events_api(request):
    """Return JSON calendar events for current user's appointments"""
    user = request.user
    if user.is_student:
        appointments = Appointment.objects.filter(student=user)
    elif user.is_staff_user:
        appointments = Appointment.objects.filter(staff=user)
    elif user.is_admin:
        appointments = Appointment.objects.all()
    else:
        appointments = Appointment.objects.none()

    status_colors = {
        'confirmed': '#00b894',
        'pending': '#f39c12',
        'completed': '#0984e3',
        'cancelled': '#d63031',
        'no_show': '#636e72',
    }

    events = []
    for a in appointments:
        title = (a.staff.get_full_name() or a.staff.username) if user.is_student else (a.student.get_full_name() or a.student.username)
        events.append({
            'id': str(a.appointment_id),
            'title': title,
            'start': f"{a.appointment_date}T{a.appointment_time}",
            'url': f"/appointments/{a.appointment_id}/",
            'backgroundColor': status_colors.get(a.status, '#6c757d'),
            'borderColor': 'transparent',
            'status': a.status,
            'reason': a.reason,
        })

    return JsonResponse(events, safe=False)

