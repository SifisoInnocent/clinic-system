from django.urls import path
from . import views

app_name = 'availability'

urlpatterns = [
    # Availability management
    path('', views.availability_list_view, name='availability_list'),
    path('add/', views.availability_create_view, name='availability_add'),
    path('create/', views.availability_create_view, name='availability_create'),
    path('<int:availability_id>/edit/', views.availability_edit_view, name='availability_edit'),
    path('<int:availability_id>/toggle/', views.availability_toggle_view, name='availability_toggle'),
    path('<int:availability_id>/delete/', views.availability_delete_view, name='availability_delete'),
    path('bulk-create/', views.availability_bulk_create_view, name='availability_bulk_create'),
    
    # Blocked periods
    path('blocked-periods/', views.blocked_period_list_view, name='blocked_period_list'),
    path('blocked-periods/create/', views.blocked_period_create_view, name='blocked_period_create'),
    path('blocked-periods/<int:blocked_period_id>/edit/', views.blocked_period_edit_view, name='blocked_period_edit'),
    path('blocked-periods/<int:blocked_period_id>/toggle/', views.blocked_period_toggle_view, name='blocked_period_toggle'),
    path('blocked-periods/<int:blocked_period_id>/delete/', views.blocked_period_delete_view, name='blocked_period_delete'),
]
