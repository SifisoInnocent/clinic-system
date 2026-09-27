from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('student/', views.student_dashboard_view, name='student_dashboard'),
    path('staff/', views.staff_dashboard_view, name='staff_dashboard'),
    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
]
