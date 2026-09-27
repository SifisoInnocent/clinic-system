from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list_view, name='notification_list'),
    path('api/recent/', views.notifications_api_view, name='api_recent'),
    path('api/mark-read/', views.mark_notification_read_view, name='api_mark_all_read'),
    path('api/mark-read/<int:notification_id>/', views.mark_notification_read_view, name='api_mark_read'),
]
