from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'student_number', 'employee_id')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('Role Information'), {'fields': ('role', 'student_number', 'employee_id')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Security'), {'fields': ('is_locked', 'failed_login_attempts', 'locked_until')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'first_name', 'last_name'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined', 'failed_login_attempts', 'locked_until')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'emergency_contact_name')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'emergency_contact_name')
    
    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('Personal Information'), {'fields': ('date_of_birth', 'address')}),
        (_('Emergency Contact'), {'fields': ('emergency_contact_name', 'emergency_contact_phone')}),
        (_('Medical Information'), {'fields': ('medical_conditions', 'allergies')}),
    )
