from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('admin_info', 'action', 'target_user', 'target_object', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('admin__username', 'target_user', 'target_object', 'description', 'ip_address')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    fieldsets = (
        (None, {
            'fields': ('admin', 'action', 'target_user', 'target_object', 'description')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('timestamp',)
        }),
    )
    
    readonly_fields = ('timestamp',)
    
    def admin_info(self, obj):
        if obj.admin:
            url = reverse('admin:accounts_user_change', args=[obj.admin.id])
            return format_html('<a href="{}">{}</a>', url, obj.admin.get_full_name() or obj.admin.username)
        return format_html('<span class="text-muted">System</span>')
    admin_info.short_description = 'Admin'
    
    def has_add_permission(self, request):
        # Prevent manual creation of audit logs
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing of audit logs
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only allow deletion for superusers
        return request.user.is_superuser
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('admin')
