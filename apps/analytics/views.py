from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import admin_required
from .models import PageView
from django.db.models import Count, Avg

@admin_required
def dashboard(request):
    total_views = PageView.objects.count()
    top_pages = PageView.objects.values('path').annotate(view_count=Count('path')).order_by('-view_count')[:10]
    avg_response_time = PageView.objects.aggregate(Avg('response_time'))['response_time__avg']
    recent_views = PageView.objects.order_by('-timestamp')[:50]
    
    context = {
        'total_views': total_views,
        'top_pages': top_pages,
        'avg_response_time': avg_response_time,
        'recent_views': recent_views,
    }
    return render(request, 'analytics/dashboard.html', context)
