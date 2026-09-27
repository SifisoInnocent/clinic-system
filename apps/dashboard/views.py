from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta

from apps.accounts.decorators import student_required, staff_required, admin_required
from apps.appointments.models import Appointment
from apps.accounts.models import User


@login_required
def dashboard_view(request):
    """Main dashboard view - redirects based on role"""
    user = request.user
    
    if user.is_student():
        return student_dashboard_view(request)
    elif user.is_staff_user():
        return staff_dashboard_view(request)
    else:  # admin
        return admin_dashboard_view(request)


@student_required
def student_dashboard_view(request):
    """Student dashboard"""
    student = request.user
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        student=student,
        appointment_date__gte=timezone.now().date(),
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')[:5]
    
    # Get recent appointments
    recent_appointments = Appointment.objects.filter(
        student=student,
        appointment_date__lt=timezone.now().date()
    ).order_by('-appointment_date', '-appointment_time')[:5]
    
    # Get appointment statistics
    total_appointments = Appointment.objects.filter(student=student).count()
    completed_appointments = Appointment.objects.filter(
        student=student, 
        status='completed'
    ).count()
    cancelled_appointments = Appointment.objects.filter(
        student=student, 
        status='cancelled'
    ).count()
    no_show_appointments = Appointment.objects.filter(
        student=student, 
        status='no_show'
    ).count()
    
    # Get all available nurses and psychologists from database
    available_nurses = User.objects.filter(
        role='nurse', 
        is_active=True
    ).order_by('first_name', 'last_name')
    
    available_psychologists = User.objects.filter(
        role='psychologist', 
        is_active=True
    ).order_by('first_name', 'last_name')
    
    context = {
        'upcoming_appointments': upcoming_appointments,
        'recent_appointments': recent_appointments,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
        'no_show_appointments': no_show_appointments,
        'has_active_booking': upcoming_appointments.exists(),
        'available_nurses': available_nurses,
        'available_psychologists': available_psychologists,
    }
    
    return render(request, 'dashboard/student_dashboard.html', context)


@staff_required
def staff_dashboard_view(request):
    """Staff dashboard"""
    staff = request.user
    
    # Get today's appointments
    today = timezone.now().date()
    today_appointments = Appointment.objects.filter(
        staff=staff,
        appointment_date=today
    ).order_by('appointment_time')
    
    # Get upcoming appointments (next 7 days)
    next_week = today + timedelta(days=7)
    upcoming_appointments = Appointment.objects.filter(
        staff=staff,
        appointment_date__gt=today,
        appointment_date__lte=next_week,
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')
    
    # Get monthly statistics
    month_start = today.replace(day=1)
    month_appointments_qs = Appointment.objects.filter(
        staff=staff,
        appointment_date__gte=month_start,
        appointment_date__lte=today
    )
    
    total_month = month_appointments_qs.count()
    completed_month = month_appointments_qs.filter(status='completed').count()
    pending_month = month_appointments_qs.filter(status='pending').count()
    confirmed_month = month_appointments_qs.filter(status='confirmed').count()
    cancelled_month = month_appointments_qs.filter(status='cancelled').count()
    no_show_month = month_appointments_qs.filter(status='no_show').count()
    
    # Get all-time statistics
    all_appointments = Appointment.objects.filter(staff=staff)
    
    # Calculate all-time status counts
    all_completed = all_appointments.filter(status='completed').count()
    all_pending = all_appointments.filter(status='pending').count()
    all_confirmed = all_appointments.filter(status='confirmed').count()
    all_cancelled = all_appointments.filter(status='cancelled').count()
    all_no_show = all_appointments.filter(status='no_show').count()
    
    context = {
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'total_month': total_month,
        'completed_month': completed_month,
        'pending_month': pending_month,
        'confirmed_month': confirmed_month,
        'cancelled_month': cancelled_month,
        'no_show_month': no_show_month,
        'all_appointments_count': all_appointments.count(),
        'all_completed': all_completed,
        'all_pending': all_pending,
        'all_confirmed': all_confirmed,
        'all_cancelled': all_cancelled,
        'all_no_show': all_no_show,
        'today': today,
    }
    
    return render(request, 'dashboard/staff_dashboard.html', context)


@admin_required
def admin_dashboard_view(request):
    """Admin dashboard"""
    
    # Get overall statistics
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_staff = User.objects.filter(role__in=['nurse', 'psychologist']).count()
    total_admins = User.objects.filter(role='admin').count()
    
    # Get appointment statistics
    total_appointments = Appointment.objects.count()
    today = timezone.now().date()
    today_appointments = Appointment.objects.filter(appointment_date=today).count()
    
    # Get appointment status counts
    pending_appointments = Appointment.objects.filter(status='pending').count()
    confirmed_appointments = Appointment.objects.filter(status='confirmed').count()
    completed_appointments = Appointment.objects.filter(status='completed').count()
    cancelled_appointments = Appointment.objects.filter(status='cancelled').count()
    no_show_appointments = Appointment.objects.filter(status='no_show').count()
    
    # Get recent appointments
    recent_appointments = Appointment.objects.order_by('-created_at')[:10]
    
    # Get monthly appointment statistics (last 6 months)
    six_months_ago = today - timedelta(days=180)
    monthly_stats = []
    
    for i in range(6):
        month_start = (six_months_ago.replace(day=1) + timedelta(days=32*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_appointments = Appointment.objects.filter(
            appointment_date__gte=month_start,
            appointment_date__lte=month_end
        ).count()
        
        monthly_stats.append({
            'month': month_start.strftime('%B %Y'),
            'count': month_appointments
        })
    
    # Get staff performance statistics
    staff_stats = User.objects.filter(
        role__in=['nurse', 'psychologist']
    ).annotate(
        total_appointments=Count('staff_appointments'),
        completed_appointments=Count(
            'staff_appointments',
            filter=Q(staff_appointments__status='completed')
        ),
        no_show_appointments=Count(
            'staff_appointments',
            filter=Q(staff_appointments__status='no_show')
        )
    ).order_by('-total_appointments')
    
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_staff': total_staff,
        'total_admins': total_admins,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'confirmed_appointments': confirmed_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
        'no_show_appointments': no_show_appointments,
        'recent_appointments': recent_appointments,
        'monthly_stats': monthly_stats,
        'staff_stats': staff_stats,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)
