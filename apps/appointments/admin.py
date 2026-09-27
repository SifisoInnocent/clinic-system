from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Appointment, AppointmentHistory


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_id', 'student_info', 'staff_info', 'appointment_date', 'appointment_time', 'provider_type', 'status', 'created_at')
    list_filter = ('status', 'provider_type', 'appointment_date', 'created_at')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'student__student_number',
                     'staff__first_name', 'staff__last_name', 'reason')
    date_hierarchy = 'appointment_date'
    ordering = ('-appointment_date', '-appointment_time')
    
    fieldsets = (
        (None, {
            'fields': ('appointment_id', 'student', 'staff', 'provider_type', 'appointment_date', 'appointment_time')
        }),
        ('Details', {
            'fields': ('reason', 'status', 'notes')
        }),
        ('Notifications', {
            'fields': ('notification_sent', 'reminder_sent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('appointment_id', 'created_at', 'updated_at')
    
    def student_info(self, obj):
        if obj.student:
            url = reverse('admin:accounts_user_change', args=[obj.student.id])
            return format_html('<a href="{}">{} ({})</a>', url, obj.student.get_full_name(), obj.student.student_number or 'N/A')
        return '-'
    student_info.short_description = 'Student'
    
    def staff_info(self, obj):
        if obj.staff:
            url = reverse('admin:accounts_user_change', args=[obj.staff.id])
            return format_html('<a href="{}">{} ({})</a>', url, obj.staff.get_full_name(), obj.staff.employee_id or 'N/A')
        return '-'
    staff_info.short_description = 'Staff'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'staff')


@admin.register(AppointmentHistory)
class AppointmentHistoryAdmin(admin.ModelAdmin):
    list_display = ('appointment_link', 'action', 'old_status', 'new_status', 'changed_by', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('appointment__appointment_id', 'changed_by__username', 'notes')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    fieldsets = (
        (None, {
            'fields': ('appointment', 'action', 'old_status', 'new_status', 'changed_by', 'notes')
        }),
        ('Timestamps', {
            'fields': ('timestamp',)
        }),
    )
    
    readonly_fields = ('timestamp',)
    
    def appointment_link(self, obj):
        if obj.appointment:
            url = reverse('admin:appointments_appointment_change', args=[obj.appointment.id])
            return format_html('<a href="{}">Appointment #{}</a>', url, obj.appointment.appointment_id)
        return '-'
    appointment_link.short_description = 'Appointment'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('appointment', 'changed_by')
