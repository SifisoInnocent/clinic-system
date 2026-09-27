import time
from .models import PageView

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Don't log static/media files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return response
            
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
            
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log view asynchronously (in a real app you might use Celery, here we just do it sync)
        PageView.objects.create(
            user=request.user if request.user.is_authenticated else None,
            path=request.path,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            method=request.method,
            status_code=response.status_code,
            response_time=response_time
        )
        
        return response
