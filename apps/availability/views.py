from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q

from .models import Availability, BlockedPeriod
from .forms import AvailabilityForm, AvailabilityBulkForm, BlockedPeriodForm
from apps.accounts.decorators import staff_required, admin_required, admin_or_staff_required
from apps.accounts.models import User
from apps.audit.models import AuditLog


@staff_required
def availability_list_view(request):
    """List staff availability"""
    availabilities = Availability.objects.filter(staff=request.user).order_by('day_of_week', 'start_time')
    
    context = {
        'availabilities': availabilities,
        'staff_user': request.user,
    }
    return render(request, 'availability/availability_list.html', context)


@staff_required
def availability_create_view(request):
    """Create new availability"""
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.staff = request.user
            
            try:
                # This will call full_clean() inside save()
                availability.save()
                
                # Log availability creation
                AuditLog.log_action(
                    admin=request.user,
                    action='create_availability',
                    target_object=f'Availability for {availability.get_day_of_week_display()}',
                    description=f"Staff {request.user.username} created availability: {availability.get_day_of_week_display()} {availability.start_time}-{availability.end_time}",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, 'Availability has been created successfully!')
                return redirect('availability:availability_list')
            except Exception as e:
                # Catch ValidationError from model full_clean()
                from django.core.exceptions import ValidationError
                if isinstance(e, ValidationError):
                    for field, errs in e.message_dict.items() if hasattr(e, 'message_dict') else [(None, e.messages)]:
                        for err in errs:
                            form.add_error(field if field != '__all__' else None, err)
                else:
                    form.add_error(None, f"Error saving availability: {e}")
    else:
        form = AvailabilityForm()
    
    return render(request, 'availability/availability_form.html', {
        'form': form,
        'title': 'Create Availability'
    })


@staff_required
def availability_edit_view(request, availability_id):
    """Edit availability"""
    availability = get_object_or_404(Availability, id=availability_id, staff=request.user)
    
    if request.method == 'POST':
        form = AvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            old_values = f"{availability.get_day_of_week_display()} {availability.start_time}-{availability.end_time}"
            
            try:
                form.save()
                
                # Log availability update
                AuditLog.log_action(
                    admin=request.user,
                    action='update_availability',
                    target_object=f'Availability for {availability.get_day_of_week_display()}',
                    description=f"Staff {request.user.username} updated availability: {old_values} to {availability.get_day_of_week_display()} {availability.start_time}-{availability.end_time}",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, 'Availability has been updated successfully!')
                return redirect('availability:availability_list')
            except Exception as e:
                from django.core.exceptions import ValidationError
                if isinstance(e, ValidationError):
                    for field, errs in e.message_dict.items() if hasattr(e, 'message_dict') else [(None, e.messages)]:
                        for err in errs:
                            form.add_error(field if field != '__all__' else None, err)
                else:
                    form.add_error(None, f"Error saving availability: {e}")
    else:
        form = AvailabilityForm(instance=availability)
    
    return render(request, 'availability/availability_form.html', {
        'form': form,
        'title': 'Edit Availability',
        'availability': availability
    })


@staff_required
@require_POST
def availability_toggle_view(request, availability_id):
    """Toggle availability active status"""
    availability = get_object_or_404(Availability, id=availability_id, staff=request.user)
    availability.is_active = not availability.is_active
    availability.save()
    
    status = 'activated' if availability.is_active else 'deactivated'
    messages.success(request, f'Availability has been {status}.')
    return redirect('availability:availability_list')


@staff_required
@require_POST
def availability_delete_view(request, availability_id):
    """Delete availability"""
    availability = get_object_or_404(Availability, id=availability_id, staff=request.user)
    
    # Check if there are future appointments for this availability
    from apps.appointments.models import Appointment
    future_appointments = Appointment.objects.filter(
        staff=request.user,
        appointment_date__gte=timezone.now().date(),
        status__in=['pending', 'confirmed']
    ).filter(
        appointment_date__week_day=availability.day_of_week + 1  # Django uses 1-7, Python uses 0-6
    ).filter(
        appointment_time__gte=availability.start_time,
        appointment_time__lt=availability.end_time
    )
    
    if future_appointments.exists():
        messages.error(request, 'Cannot delete availability with future appointments. Cancel or reschedule appointments first.')
        return redirect('availability:availability_list')
    
    # Log availability deletion
    AuditLog.log_action(
        admin=request.user,
        action='delete_availability',
        target_object=f'Availability for {availability.get_day_of_week_display()}',
        description=f"Staff {request.user.username} deleted availability: {availability.get_day_of_week_display()} {availability.start_time}-{availability.end_time}",
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    availability.delete()
    messages.success(request, 'Availability has been deleted successfully!')
    return redirect('availability:availability_list')


@staff_required
def availability_bulk_create_view(request):
    """Create availability for multiple days at once"""
    if request.method == 'POST':
        form = AvailabilityBulkForm(request.POST)
        if form.is_valid():
            days = form.cleaned_data['days']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            
            created_count = 0
            errors = []
            for day in days:
                # Check if availability already exists
                existing = Availability.objects.filter(
                    staff=request.user,
                    day_of_week=day,
                    start_time=start_time,
                    end_time=end_time
                ).first()
                
                if not existing:
                    try:
                        avail = Availability(
                            staff=request.user,
                            day_of_week=day,
                            start_time=start_time,
                            end_time=end_time
                        )
                        avail.save()
                        created_count += 1
                    except Exception as e:
                        from django.core.exceptions import ValidationError
                        if isinstance(e, ValidationError):
                            # Collect error messages
                            msgs = []
                            if hasattr(e, 'message_dict'):
                                for f, errs in e.message_dict.items():
                                    msgs.extend(errs)
                            else:
                                msgs.extend(e.messages)
                            day_name = dict(Availability.DAY_CHOICES).get(int(day), day)
                            errors.append(f"{day_name}: {', '.join(msgs)}")
            
            if created_count > 0:
                # Log bulk creation
                AuditLog.log_action(
                    admin=request.user,
                    action='create_availability',
                    target_object=f'Bulk Availability',
                    description=f"Staff {request.user.username} created {created_count} availability slots",
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                messages.success(request, f'{created_count} availability slots have been created successfully!')
            
            if errors:
                for err in errors:
                    messages.error(request, err)
                
            if created_count > 0 and not errors:
                return redirect('availability:availability_list')
    else:
        form = AvailabilityBulkForm()
    
    return render(request, 'availability/availability_bulk.html', {
        'form': form,
        'title': 'Create Bulk Availability'
    })


@admin_or_staff_required
def blocked_period_list_view(request):
    """List blocked periods"""
    if request.user.is_admin():
        blocked_periods = BlockedPeriod.objects.all().order_by('start_datetime')
    else:
        blocked_periods = BlockedPeriod.objects.filter(staff=request.user).order_by('start_datetime')
    
    context = {
        'blocked_periods': blocked_periods,
        'staff_user': request.user,
        'is_admin': request.user.is_admin(),
    }
    return render(request, 'availability/blocked_period_list.html', context)


@admin_or_staff_required
def blocked_period_create_view(request):
    """Create new blocked period"""
    if request.method == 'POST':
        form = BlockedPeriodForm(request.POST)
        if form.is_valid():
            blocked_period = form.save(commit=False)
            if request.user.is_staff_user():
                blocked_period.staff = request.user
            else:
                staff_id = request.POST.get('staff_id')
                if staff_id:
                    blocked_period.staff = get_object_or_404(User, id=staff_id)
                else:
                    first_staff = User.objects.filter(role__in=['nurse', 'psychologist']).first()
                    if first_staff:
                        blocked_period.staff = first_staff
                    else:
                        messages.error(request, 'No clinic staff available to assign blocked period.')
                        return redirect('availability:blocked_period_list')
            
            blocked_period.save()
            
            # Log blocked period creation
            AuditLog.log_action(
                admin=request.user,
                action='create_blocked_period',
                target_object=f'Blocked Period: {blocked_period.reason}',
                description=f"{request.user.username} created blocked period: {blocked_period.reason} from {blocked_period.start_datetime} to {blocked_period.end_datetime}",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, 'Blocked period has been created successfully!')
            return redirect('availability:blocked_period_list')
    else:
        form = BlockedPeriodForm()
    
    return render(request, 'availability/blocked_period_form.html', {
        'form': form,
        'title': 'Create Blocked Period'
    })


@admin_or_staff_required
def blocked_period_edit_view(request, blocked_period_id):
    """Edit blocked period"""
    if request.user.is_admin():
        blocked_period = get_object_or_404(BlockedPeriod, id=blocked_period_id)
    else:
        blocked_period = get_object_or_404(BlockedPeriod, id=blocked_period_id, staff=request.user)
    
    if request.method == 'POST':
        form = BlockedPeriodForm(request.POST, instance=blocked_period)
        if form.is_valid():
            old_values = f"{blocked_period.reason}: {blocked_period.start_datetime} to {blocked_period.end_datetime}"
            form.save()
            
            # Log blocked period update
            AuditLog.log_action(
                admin=request.user,
                action='update_blocked_period',
                target_object=f'Blocked Period: {blocked_period.reason}',
                description=f"{request.user.username} updated blocked period: {old_values} to {blocked_period.reason}: {blocked_period.start_datetime} to {blocked_period.end_datetime}",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, 'Blocked period has been updated successfully!')
            return redirect('availability:blocked_period_list')
    else:
        form = BlockedPeriodForm(instance=blocked_period)
    
    return render(request, 'availability/blocked_period_form.html', {
        'form': form,
        'title': 'Edit Blocked Period',
        'blocked_period': blocked_period
    })


@admin_or_staff_required
@require_POST
def blocked_period_toggle_view(request, blocked_period_id):
    """Toggle blocked period active status"""
    if request.user.is_admin():
        blocked_period = get_object_or_404(BlockedPeriod, id=blocked_period_id)
    else:
        blocked_period = get_object_or_404(BlockedPeriod, id=blocked_period_id, staff=request.user)
    
    blocked_period.is_active = not blocked_period.is_active
    blocked_period.save()
    
    status = 'activated' if blocked_period.is_active else 'deactivated'
    messages.success(request, f'Blocked period has been {status}.')
    return redirect('availability:blocked_period_list')


@admin_or_staff_required
@require_POST
def blocked_period_delete_view(request, blocked_period_id):
    """Delete blocked period"""
    if request.user.is_admin():
        blocked_period = get_object_or_404(BlockedPeriod, id=blocked_period_id)
    else:
        blocked_period = get_object_or_404(BlockedPeriod, id=blocked_period_id, staff=request.user)
    
    # Check if there are future appointments during this period
    from apps.appointments.models import Appointment
    future_appointments = Appointment.objects.filter(
        staff=blocked_period.staff,
        appointment_date__gte=blocked_period.start_datetime.date(),
        appointment_date__lte=blocked_period.end_datetime.date(),
        status__in=['pending', 'confirmed']
    ).filter(
        Q(appointment_date=blocked_period.start_datetime.date(), appointment_time__gte=blocked_period.start_datetime.time()) |
        Q(appointment_date=blocked_period.end_datetime.date(), appointment_time__lte=blocked_period.end_datetime.time())
    )
    
    if future_appointments.exists():
        messages.error(request, 'Cannot delete blocked period with future appointments. Cancel or reschedule appointments first.')
        return redirect('availability:blocked_period_list')
    
    # Log blocked period deletion
    AuditLog.log_action(
        admin=request.user,
        action='delete_blocked_period',
        target_object=f'Blocked Period: {blocked_period.reason}',
        description=f"{request.user.username} deleted blocked period: {blocked_period.reason}",
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    blocked_period.delete()
    messages.success(request, 'Blocked period has been deleted successfully!')
    return redirect('availability:blocked_period_list')


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
