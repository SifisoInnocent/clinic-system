from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_view, name='reports'),
    path('appointments/', views.appointment_report_view, name='appointment_report'),
    path('users/', views.user_report_view, name='user_report'),
    path('statistics/', views.statistics_report_view, name='statistics_report'),
    path('unattended/', views.unattended_report_view, name='unattended_report'),
]
