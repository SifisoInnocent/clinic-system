from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
import csv
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO

from apps.accounts.decorators import admin_required
from apps.appointments.models import Appointment
from apps.accounts.models import User


@admin_required
def reports_view(request):
    """Main reports page"""
    return render(request, 'reports/reports.html')


@admin_required
def appointment_report_view(request):
    """Generate appointment reports"""
    if request.method == 'POST':
        form_data = request.POST
        report_type = form_data.get('report_type')
        date_from = form_data.get('date_from')
        date_to = form_data.get('date_to')
        format_type = form_data.get('format', 'html')
        
        # Validate dates
        if date_from and date_to:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Invalid date format')
                return redirect('reports:reports')
        else:
            # Default to last 30 days
            date_to = timezone.now().date()
            date_from = date_to - timedelta(days=30)
        
        # Get appointments based on date range
        appointments = Appointment.objects.filter(
            appointment_date__gte=date_from,
            appointment_date__lte=date_to
        )
        
        # Apply filters based on report type
        if report_type in ['bookings', 'pending', 'confirmed']:
            appointments = appointments.filter(status__in=['pending', 'confirmed'])
        elif report_type == 'cancellations':
            appointments = appointments.filter(status='cancelled')
        elif report_type in ['no_shows', 'no-shows']:
            appointments = appointments.filter(status='no_show')
        elif report_type == 'completed':
            appointments = appointments.filter(status='completed')
        # 'all', 'summary', 'detailed' include all appointments in the range
        
        # Generate report based on format
        if format_type == 'pdf':
            return generate_pdf_report(appointments, report_type, date_from, date_to)
        elif format_type == 'csv':
            return generate_csv_report(appointments, report_type, date_from, date_to)
        else:
            # HTML preview
            context = {
                'appointments': appointments.order_by('-appointment_date'),
                'report_type': report_type,
                'date_from': date_from,
                'date_to': date_to,
                'total_count': appointments.count(),
            }
            return render(request, 'reports/appointment_report_preview.html', context)
    
    return redirect('reports:reports')


@admin_required
def user_report_view(request):
    """Generate user reports"""
    if request.method == 'POST':
        form_data = request.POST
        user_type = form_data.get('user_type')
        format_type = form_data.get('format', 'html')
        
        # Get users based on type
        if user_type in ['students', 'student']:
            users = User.objects.filter(role='student')
        elif user_type in ['staff', 'nurses', 'psychologists']:
            users = User.objects.filter(role__in=['nurse', 'psychologist'])
        elif user_type in ['admins', 'admin']:
            users = User.objects.filter(role='admin')
        else:
            users = User.objects.all()
        
        # Generate report based on format
        if format_type == 'pdf':
            return generate_user_pdf_report(users, user_type)
        elif format_type == 'csv':
            return generate_user_csv_report(users, user_type)
        else:
            # HTML preview
            context = {
                'users': users.order_by('-date_joined'),
                'user_type': user_type,
                'total_count': users.count(),
            }
            return render(request, 'reports/user_report_preview.html', context)
    
    return redirect('reports:reports')


@admin_required
def statistics_report_view(request):
    """Generate statistics report"""
    # Support both GET and POST requests for date range
    date_from = request.POST.get('date_from') or request.GET.get('date_from')
    date_to = request.POST.get('date_to') or request.GET.get('date_to')
    
    if date_from and date_to:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            date_to = timezone.now().date()
            date_from = date_to - timedelta(days=30)
    else:
        date_to = timezone.now().date()
        date_from = date_to - timedelta(days=30)
    
    # Get statistics
    appointments = Appointment.objects.filter(
        appointment_date__gte=date_from,
        appointment_date__lte=date_to
    )
    
    # Status breakdown
    status_stats = appointments.values('status').annotate(
        count=Count('pk')
    ).order_by('status')
    
    # Provider type breakdown
    provider_stats = appointments.values('staff__role', 'staff__first_name', 'staff__last_name').annotate(
        count=Count('pk'),
        completed=Count('pk', filter=Q(status='completed')),
        no_show=Count('pk', filter=Q(status='no_show'))
    ).order_by('-count')
    
    # Daily statistics
    daily_stats = []
    current_date = date_from
    while current_date <= date_to:
        day_appointments = appointments.filter(appointment_date=current_date)
        daily_stats.append({
            'date': current_date,
            'total': day_appointments.count(),
            'completed': day_appointments.filter(status='completed').count(),
            'cancelled': day_appointments.filter(status='cancelled').count(),
            'no_show': day_appointments.filter(status='no_show').count(),
        })
        current_date += timedelta(days=1)
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_appointments': appointments.count(),
        'status_stats': status_stats,
        'provider_stats': provider_stats,
        'daily_stats': daily_stats,
    }
    
    return render(request, 'reports/statistics_report.html', context)


def generate_pdf_report(appointments, report_type, date_from, date_to):
    """Generate PDF report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    report_titles = {
        'bookings': 'Bookings Report',
        'cancellations': 'Cancellations Report',
        'no_shows': 'No-Shows Report',
        'completed': 'Completed Appointments Report',
        'all': 'All Appointments Report'
    }
    
    title = report_titles.get(report_type, 'Appointments Report')
    elements.append(Paragraph(title, title_style))
    
    # Date range
    date_style = ParagraphStyle(
        'DateRange',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1
    )
    elements.append(Paragraph(f"Period: {date_from} to {date_to}", date_style))
    elements.append(Spacer(1, 20))
    
    # Table data
    data = [['ID', 'Student', 'Student ID', 'Staff', 'Type', 'Date', 'Time', 'Status']]
    
    for appointment in appointments.order_by('-appointment_date'):
        data.append([
            str(appointment.appointment_id),
            appointment.student.get_full_name(),
            appointment.student.student_number or 'N/A',
            appointment.staff.get_full_name(),
            appointment.get_provider_type_display(),
            str(appointment.appointment_date),
            str(appointment.appointment_time),
            appointment.get_status_display()
        ])
    
    # Create table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Summary
    elements.append(Spacer(1, 20))
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=12,
        spaceBefore=20
    )
    elements.append(Paragraph(f"Total Appointments: {appointments.count()}", summary_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{title}_{date_from}_{date_to}.pdf"'
    return response


def generate_csv_report(appointments, report_type, date_from, date_to):
    """Generate CSV report"""
    response = HttpResponse(content_type='text/csv')
    report_titles = {
        'bookings': 'Bookings',
        'cancellations': 'Cancellations',
        'no_shows': 'No-Shows',
        'completed': 'Completed',
        'all': 'All_Appointments'
    }
    
    title = report_titles.get(report_type, 'Appointments')
    filename = f"{title}_{date_from}_{date_to}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Appointment ID', 'Student Name', 'Student ID', 'Staff Name', 
        'Provider Type', 'Appointment Date', 'Appointment Time', 'Status', 
        'Reason', 'Created At'
    ])
    
    for appointment in appointments.order_by('-appointment_date'):
        writer.writerow([
            appointment.appointment_id,
            appointment.student.get_full_name(),
            appointment.student.student_number or '',
            appointment.staff.get_full_name(),
            appointment.get_provider_type_display(),
            appointment.appointment_date,
            appointment.appointment_time,
            appointment.get_status_display(),
            appointment.reason,
            appointment.created_at
        ])
    
    return response


def generate_user_pdf_report(users, user_type):
    """Generate user PDF report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1
    )
    
    report_titles = {
        'students': 'Students Report',
        'staff': 'Staff Report',
        'admins': 'Administrators Report',
        'all': 'All Users Report'
    }
    
    title = report_titles.get(user_type, 'Users Report')
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 20))
    
    # Table data
    data = [['Username', 'Name', 'Email', 'Role', 'Student/Employee ID', 'Phone', 'Status']]
    
    for user in users.order_by('-date_joined'):
        data.append([
            user.username,
            user.get_full_name(),
            user.email,
            user.get_role_display(),
            user.student_number or user.employee_id or 'N/A',
            user.phone_number or 'N/A',
            'Active' if user.is_active else 'Inactive'
        ])
    
    # Create table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Summary
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=12,
        spaceBefore=20
    )
    elements.append(Paragraph(f"Total Users: {users.count()}", summary_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{title}.pdf"'
    return response


def generate_user_csv_report(users, user_type):
    """Generate user CSV report"""
    response = HttpResponse(content_type='text/csv')
    report_titles = {
        'students': 'Students',
        'staff': 'Staff',
        'admins': 'Administrators',
        'all': 'All_Users'
    }
    
    title = report_titles.get(user_type, 'Users')
    filename = f"{title}_Report.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Username', 'First Name', 'Last Name', 'Email', 'Role', 
        'Student/Employee ID', 'Phone Number', 'Is Active', 
        'Date Joined'
    ])
    
    for user in users.order_by('-date_joined'):
        writer.writerow([
            user.username,
            user.first_name,
            user.last_name,
            user.email,
            user.get_role_display(),
            user.student_number or user.employee_id or '',
            user.phone_number or '',
            user.is_active,
            user.date_joined
        ])
    
    return response

@admin_required
def unattended_report_view(request):
    """Report for students with unattended (no-show) appointments"""
    from django.db.models import Count, Q
    from apps.accounts.models import User
    
    # Get students with at least one no-show, annotate with count
    students = User.objects.filter(
        role='student',
        student_appointments__status='no_show'
    ).annotate(
        missed_count=Count('student_appointments', filter=Q(student_appointments__status='no_show'))
    ).order_by('-missed_count')
    
    context = {
        'students': students,
    }
    return render(request, 'reports/unattended_report.html', context)
