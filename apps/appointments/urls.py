from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list_view, name='appointment_list'),
    path('book/', views.appointment_book_view, name='appointment_book'),
    path('<int:appointment_id>/', views.appointment_detail_view, name='appointment_detail'),
    path('<int:appointment_id>/slip/', views.appointment_slip_view, name='appointment_slip'),
    path('<int:appointment_id>/cancel/', views.appointment_cancel_view, name='appointment_cancel'),
    path('<int:appointment_id>/reschedule/', views.appointment_reschedule_view, name='appointment_reschedule'),
    path('<int:appointment_id>/update-status/', views.appointment_update_status_view, name='appointment_update_status'),
    path('api/available-slots/', views.get_available_slots_view, name='get_available_slots'),
    path('api/staff-by-type/', views.get_staff_by_type_view, name='get_staff_by_type'),
    path('api/events/', views.appointment_events_api, name='appointment_events_api'),
]
