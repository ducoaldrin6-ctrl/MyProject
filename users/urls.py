from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('account/', views.account_settings, name='account_settings'),
    path('students/', views.students_list, name='students_list'),
    path('attendance-list/', views.attendance_list, name='attendance_list'),
]