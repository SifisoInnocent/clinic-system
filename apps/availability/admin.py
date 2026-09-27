from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Availability, BlockedPeriod


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('staff_info', 'day_of_week', 'start_time', 'end_time', 'is_active')
    list_filter = ('day_of_week', 'is_active', 'staff__role')
    search_fields = ('staff__username', 'staff__first_name', 'staff__last_name')
    ordering = ('staff__last_name', 'day_of_week', 'start_time')
    
    fieldsets = (
        (None, {
            'fields': ('staff', 'day_of_week', 'start_time', 'end_time', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def staff_info(self, obj):
        if obj.staff:
            url = reverse('admin:accounts_user_change', args=[obj.staff.id])
            return format_html('<a href="{}">{} ({})</a>', url, obj.staff.get_full_name(), obj.staff.get_role_display())
        return '-'
    staff_info.short_description = 'Staff'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('staff')


@admin.register(BlockedPeriod)
class BlockedPeriodAdmin(admin.ModelAdmin):
    list_display = ('staff_info', 'start_datetime', 'end_datetime', 'reason', 'is_active', 'is_current')
    list_filter = ('is_active', 'reason', 'staff__role')
    search_fields = ('staff__username', 'staff__first_name', 'staff__last_name', 'reason')
    ordering = ('-start_datetime',)
    
    fieldsets = (
        (None, {
            'fields': ('staff', 'start_datetime', 'end_datetime', 'reason', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def staff_info(self, obj):
        if obj.staff:
            url = reverse('admin:accounts_user_change', args=[obj.staff.id])
            return format_html('<a href="{}">{} ({})</a>', url, obj.staff.get_full_name(), obj.staff.get_role_display())
        return '-'
    staff_info.short_description = 'Staff'
    
    def is_current(self, obj):
        from django.utils import timezone
        if obj.is_active and obj.start_datetime <= timezone.now() <= obj.end_datetime:
            return format_html('<span class="badge bg-success">Current</span>')
        elif obj.is_active and obj.start_datetime > timezone.now():
            return format_html('<span class="badge bg-warning">Future</span>')
        elif obj.is_active:
            return format_html('<span class="badge bg-secondary">Past</span>')
        else:
            return format_html('<span class="badge bg-danger">Inactive</span>')
    is_current.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('staff')
