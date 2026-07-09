from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Application, AuditLog, AttendanceRecord, OTPCode, Scholar, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')


@admin.register(Scholar)
class ScholarAdmin(admin.ModelAdmin):
    list_display = ('scholar_id', 'first_name', 'last_name', 'sex', 'course', 'year_level', 'status', 'assigned_to')
    list_filter = ('status', 'sex', 'course', 'year_level')
    search_fields = ('scholar_id', 'first_name', 'last_name', 'email', 'course')
    autocomplete_fields = ('assigned_to',)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('scholar', 'attendance_date', 'status', 'created_at')
    list_filter = ('status', 'attendance_date')
    search_fields = ('scholar__scholar_id', 'scholar__first_name', 'scholar__last_name')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'scholar', 'status', 'commitment_amount', 'submitted_by', 'reviewed_by', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('application_id', 'scholar__scholar_id', 'scholar__first_name', 'scholar__last_name')
    readonly_fields = ('submitted_at', 'reviewed_at', 'updated_at')


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'is_used')
    list_filter = ('is_used',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'created_at')
    readonly_fields = ('user', 'action', 'ip_address', 'created_at')
    ordering = ('-created_at',)
