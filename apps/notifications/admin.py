from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import NotificationLog, NotificationTemplate


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('type', 'recipient', 'purpose', 'appointment_link', 'status', 'sent_at', 'created_at')
    list_filter = ('type', 'purpose', 'status', 'created_at')
    search_fields = ('recipient', 'appointment__appointment_id', 'error_message')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('type', 'recipient', 'appointment', 'purpose', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'sent_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    readonly_fields = ('created_at', 'sent_at')
    
    def appointment_link(self, obj):
        if obj.appointment:
            url = reverse('admin:appointments_appointment_change', args=[obj.appointment.id])
            return format_html('<a href="{}">#{}</a>', url, obj.appointment.appointment_id)
        return '-'
    appointment_link.short_description = 'Appointment'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('appointment')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('type', 'purpose', 'is_active', 'created_at', 'updated_at')
    list_filter = ('type', 'purpose', 'is_active')
    search_fields = ('purpose', 'subject_template', 'message_template')
    ordering = ('type', 'purpose')
    
    fieldsets = (
        (None, {
            'fields': ('type', 'purpose', 'subject_template', 'message_template', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
