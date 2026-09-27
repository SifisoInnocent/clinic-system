from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.timesince import timesince
from django.utils import timezone

from .models import NotificationLog


def get_user_notifications_qs(user):
    """Get queryset of notifications relevant to this user"""
    if user.is_admin():
        return NotificationLog.objects.all().order_by('-created_at')
    
    q_filter = Q(recipient=user.email)
    if user.phone_number:
        q_filter |= Q(recipient=user.phone_number)
    
    if user.is_student():
        q_filter |= Q(appointment__student=user)
    elif user.is_staff_user():
        q_filter |= Q(appointment__staff=user)
        
    return NotificationLog.objects.filter(q_filter).distinct().order_by('-created_at')


@login_required
def notifications_api_view(request):
    """JSON API endpoint returning user's recent notifications and unread count"""
    qs = get_user_notifications_qs(request.user)
    unread_count = qs.filter(is_read=False).count()
    recent = qs[:10]
    
    data = []
    for n in recent:
        data.append({
            'id': n.id,
            'type': n.type,
            'purpose': n.purpose,
            'purpose_display': n.get_purpose_display(),
            'subject': n.subject,
            'message': n.message[:120] + ('...' if len(n.message) > 120 else ''),
            'is_read': n.is_read,
            'status': n.status,
            'time_ago': f"{timesince(n.created_at, timezone.now()).split(',')[0]} ago",
            'appointment_id': n.appointment_id if n.appointment else None,
        })
        
    return JsonResponse({
        'status': 'success',
        'unread_count': unread_count,
        'notifications': data
    })


@login_required
@require_POST
def mark_notification_read_view(request, notification_id=None):
    """Mark a single notification or all user notifications as read"""
    qs = get_user_notifications_qs(request.user)
    
    if notification_id:
        notification = get_object_or_404(qs, id=notification_id)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    else:
        qs.filter(is_read=False).update(is_read=True)
        
    unread_count = qs.filter(is_read=False).count()
    return JsonResponse({
        'status': 'success',
        'unread_count': unread_count
    })


@login_required
def notification_list_view(request):
    """Full notifications page with pagination"""
    qs = get_user_notifications_qs(request.user)
    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    unread_count = qs.filter(is_read=False).count()
    
    return render(request, 'notifications/notification_list.html', {
        'notifications': page_obj,
        'unread_count': unread_count,
        'is_student': request.user.is_student(),
        'is_staff': request.user.is_staff_user(),
        'is_admin': request.user.is_admin(),
    })
