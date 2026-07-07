from django.urls import path
from .views import (
    ApplicationListAPIView,
    StudentProfileListAPIView,
    AttendanceListAPIView,
)

urlpatterns = [
    path('applications/', ApplicationListAPIView.as_view(), name='api-applications'),
    path('students/', StudentProfileListAPIView.as_view(), name='api-students'),
    path('attendance/', AttendanceListAPIView.as_view(), name='api-attendance'),
]
