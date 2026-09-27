from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from apps.accounts.decorators import admin_required
from .models import AuditLog


@admin_required
def audit_log_view(request):
    """View audit logs"""
    logs = AuditLog.objects.all().order_by('-timestamp')
    
    # Apply filters
    action_filter = request.GET.get('action')
    admin_filter = request.GET.get('admin')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('search')
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if admin_filter:
        logs = logs.filter(admin__username=admin_filter)
    
    if date_from:
        try:
            from datetime import datetime
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            from datetime import datetime
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__date__lte=date_to)
        except ValueError:
            pass
    
    if search_query:
        logs = logs.filter(
            Q(target_user__icontains=search_query) |
            Q(target_object__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    action_choices = AuditLog.ACTION_CHOICES
    admin_choices = set(log.admin.username for log in logs if log.admin)
    
    context = {
        'logs': page_obj,
        'action_choices': action_choices,
        'admin_choices': sorted(admin_choices),
        'action_filter': action_filter,
        'admin_filter': admin_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }
    
    return render(request, 'audit/audit_log.html', context)
