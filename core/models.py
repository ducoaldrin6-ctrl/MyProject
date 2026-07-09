from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')


class Scholar(models.Model):
    SCHOLARSHIP_STATUS = [
        ('active', 'Active'),
        ('probation', 'Probation'),
        ('inactive', 'Inactive'),
    ]
    YEAR_LEVELS = [(str(i), f'Year {i}') for i in range(1, 5)]
    SEX_CHOICES = [
        ('female', 'Female'),
        ('male', 'Male'),
        ('other', 'Other'),
    ]

    scholar_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=20, choices=SEX_CHOICES, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    course = models.CharField(max_length=100)
    year_level = models.CharField(max_length=4, choices=YEAR_LEVELS)
    status = models.CharField(max_length=20, choices=SCHOLARSHIP_STATUS, default='active')
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_scholars',
        limit_choices_to={'role': 'staff'},
    )
    date_enrolled = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_enrolled', 'last_name', 'first_name']

    def __str__(self):
        return f"{self.scholar_id} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def age(self):
        today = timezone.localdate()
        years = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            years -= 1
        return years


class AttendanceRecord(models.Model):
    ATTENDANCE_STATUS = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    scholar = models.ForeignKey(Scholar, on_delete=models.CASCADE, related_name='attendance_records')
    attendance_date = models.DateField()
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='present')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('scholar', 'attendance_date')
        ordering = ['-attendance_date', 'scholar__last_name', 'scholar__first_name']

    def __str__(self):
        return f"{self.scholar} - {self.attendance_date} - {self.status}"


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]
    scholar = models.ForeignKey(Scholar, on_delete=models.CASCADE, related_name='applications')
    application_id = models.CharField(max_length=30, unique=True)
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_applications',
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications',
    )
    student_notes = models.TextField(blank=True)
    parent_name = models.CharField(max_length=120)
    parent_relation = models.CharField(max_length=60)
    parent_phone = models.CharField(max_length=20)
    parent_email = models.EmailField()
    guardian_name = models.CharField(max_length=120, blank=True)
    guardian_relation = models.CharField(max_length=60, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    guardian_email = models.EmailField(blank=True)
    commitment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at', 'status', 'scholar__last_name']

    def __str__(self):
        return f"Application {self.application_id} - {self.scholar}"


class OTPCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.username} - {self.code}"


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"
