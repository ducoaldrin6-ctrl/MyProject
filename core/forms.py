from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Application, AttendanceRecord, Scholar, User


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your username',
            'autocomplete': 'username',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'username': 'Choose a username',
            'email': 'Your email for OTP codes',
            'first_name': 'First name',
            'last_name': 'Last name',
            'password1': 'Create a password',
            'password2': 'Confirm your password',
        }
        for name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control form-control-lg',
                'placeholder': placeholders.get(name, ''),
            })
        self.fields['email'].required = True
        self.fields['password1'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['password2'].widget.attrs['autocomplete'] = 'new-password'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'staff'
        user.email = self.cleaned_data['email']
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class ScholarForm(forms.ModelForm):
    class Meta:
        model = Scholar
        fields = [
            'scholar_id',
            'first_name',
            'last_name',
            'date_of_birth',
            'sex',
            'address',
            'email',
            'phone',
            'course',
            'year_level',
            'status',
            'assigned_to',
            'date_enrolled',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_enrolled': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'course': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'year_level': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'scholar_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data['date_of_birth']
        if date_of_birth >= timezone.localdate():
            raise ValidationError('Date of birth must be in the past.')
        return date_of_birth


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = AttendanceRecord
        fields = ['scholar', 'attendance_date', 'status', 'notes']
        widgets = {
            'scholar': forms.Select(attrs={'class': 'form-select'}),
            'attendance_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_attendance_date(self):
        attendance_date = self.cleaned_data['attendance_date']
        if attendance_date > timezone.localdate():
            raise ValidationError('Attendance date cannot be in the future.')
        return attendance_date


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            'scholar',
            'application_id',
            'student_notes',
            'parent_name',
            'parent_relation',
            'parent_phone',
            'parent_email',
            'guardian_name',
            'guardian_relation',
            'guardian_phone',
            'guardian_email',
            'commitment_amount',
            'remarks',
        ]
        widgets = {
            'scholar': forms.Select(attrs={'class': 'form-select'}),
            'application_id': forms.TextInput(attrs={'class': 'form-control'}),
            'student_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'commitment_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_commitment_amount(self):
        amount = self.cleaned_data['commitment_amount']
        if amount < 0:
            raise ValidationError('Commitment amount cannot be negative.')
        return amount

    def clean(self):
        cleaned_data = super().clean()
        guardian_fields = ['guardian_name', 'guardian_relation', 'guardian_phone', 'guardian_email']
        if any(cleaned_data.get(name) for name in guardian_fields):
            for name in guardian_fields[:3]:
                if not cleaned_data.get(name):
                    self.add_error(name, 'Complete the guardian name, relation, and phone together.')
        return cleaned_data


class ApplicationReviewForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status', 'remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class UserAccountForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text='Leave blank to keep the current password when editing.',
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.instance.pk and not password:
            raise ValidationError('Password is required for new accounts.')
        return password

    def save(self, commit=True):
        password = self.cleaned_data.pop('password', '')
        user = super().save(commit=False)
        if password:
            user.set_password(password)
        if user.role == 'admin':
            user.is_staff = True
        if commit:
            user.save()
        return user
