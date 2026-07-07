from rest_framework import generics
from applications.models import Application
from users.models import StudentProfile, Attendance
from .serializers import ApplicationSerializer, StudentProfileSerializer, AttendanceSerializer


class ApplicationListAPIView(generics.ListAPIView):
    queryset = Application.objects.select_related('user').all()
    serializer_class = ApplicationSerializer


class StudentProfileListAPIView(generics.ListAPIView):
    queryset = StudentProfile.objects.select_related('user').all()
    serializer_class = StudentProfileSerializer


class AttendanceListAPIView(generics.ListAPIView):
    queryset = Attendance.objects.select_related('user').all()
    serializer_class = AttendanceSerializer
