from django import forms
from django.contrib.auth.models import User

from .models import StudentProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['course', 'year_level', 'contact_number', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
