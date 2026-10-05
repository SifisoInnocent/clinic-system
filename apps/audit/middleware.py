import logging
from django.utils.deprecation import MiddlewareMixin
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)

class PatientDataAccessAuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # Only log staff access to patient data
        if request.user.is_staff_user() or request.user.is_admin():
            path = request.path.lower()
            
            # Simple heuristic: if the URL contains 'appointment' or 'patient' or 'student'
            # and is a read operation (GET), or it's just accessing a detail view.
            # We can log any access to specific endpoints.
            if ('appointment' in path or 'student' in path or 'patient' in path) and request.method == 'GET':
                try:
                    AuditLog.log_action(
                        admin=request.user,
                        action='access_patient_record',
                        description=f"Accessed patient/appointment data at {request.path}",
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                except Exception as e:
                    logger.error(f"Failed to log patient data access: {e}")

        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
