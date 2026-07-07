from rest_framework import serializers
from applications.models import Application
from users.models import StudentProfile, Attendance
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ApplicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'user', 'full_name', 'email', 'course', 'year_level',
            'commitment', 'statement', 'status', 'date_applied'
        ]


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields = ['id', 'user', 'course', 'year_level', 'contact_number', 'address']


class AttendanceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'user', 'date', 'status', 'notes']
