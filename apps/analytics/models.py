from django.db import models
from django.conf import settings

class PageView(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    path = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    response_time = models.FloatField(null=True, blank=True, help_text="Response time in seconds")

    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code}"

    class Meta:
        ordering = ['-timestamp']
