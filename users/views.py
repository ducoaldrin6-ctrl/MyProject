from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import UserProfileForm, StudentProfileForm
from .models import StudentProfile
from .models import Attendance
from applications.models import Application
from django.utils import timezone


@login_required
def dashboard_view(request):
    applications = Application.objects.filter(user=request.user).order_by('-date_applied')[:6]
    total_applications = applications.count()
    approved_count = Application.objects.filter(user=request.user, status='approved').count()
    pending_count = Application.objects.filter(user=request.user, status='pending').count()
    rejected_count = Application.objects.filter(user=request.user, status='rejected').count()

    return render(request, 'dashboard.html', {
        'applications': applications,
        'total_applications': total_applications,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
    })


@login_required
def profile_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    # Application status counts for the current user
    total_applications = Application.objects.filter(user=request.user).count()
    approved_count = Application.objects.filter(user=request.user, status='approved').count()
    pending_count = Application.objects.filter(user=request.user, status='pending').count()
    rejected_count = Application.objects.filter(user=request.user, status='rejected').count()

    # Attendance summary
    attendance_qs = Attendance.objects.filter(user=request.user)
    attendance_total = attendance_qs.count()
    attendance_present = attendance_qs.filter(status='present').count()
    attendance_absent = attendance_qs.filter(status='absent').count()
    recent_attendance = attendance_qs[:10]

    return render(request, 'users/student_profile.html', {
        'profile': profile,
        'total_applications': total_applications,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
        'attendance_total': attendance_total,
        'attendance_present': attendance_present,
        'attendance_absent': attendance_absent,
        'recent_attendance': recent_attendance,
    })


@login_required
def profile_edit(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=request.user)
        profile_form = StudentProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('users:profile')
    else:
        user_form = UserProfileForm(instance=request.user)
        profile_form = StudentProfileForm(instance=profile)

    return render(request, 'users/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
def attendance_view(request):
    # Simple attendance listing for the logged-in user
    attendance_qs = Attendance.objects.filter(user=request.user)[:100]
    return render(request, 'users/attendance.html', {
        'attendance_list': attendance_qs,
    })


@login_required
def account_settings(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    return render(request, 'users/account_settings.html', {
        'user': request.user,
        'profile': profile,
    })


def students_list(request):
    """List all students with search and pagination"""
    students = StudentProfile.objects.select_related('user').all().order_by('-id')

    # Search functionality (case-insensitive)
    search_query = request.GET.get('q', '').strip()
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(course__icontains=search_query) |
            Q(year_level__icontains=search_query)
        )

    # Filter by year level
    year_filter = request.GET.get('year', '').strip()
    if year_filter:
        students = students.filter(year_level__icontains=year_filter)

    # Pagination (5 items per page)
    paginator = Paginator(students, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'users/students_list.html', {
        'page_obj': page_obj,
        'students': page_obj.object_list,
        'search_query': search_query,
        'year_filter': year_filter,
        'total_count': paginator.count,
    })


def attendance_list(request):
    """List attendance records with search and pagination"""
    attendance_records = Attendance.objects.select_related('user').all().order_by('-date')

    # Search functionality (case-insensitive)
    search_query = request.GET.get('q', '').strip()
    if search_query:
        attendance_records = attendance_records.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # Filter by status
    status_filter = request.GET.get('status', '').strip()
    if status_filter in ['present', 'absent']:
        attendance_records = attendance_records.filter(status=status_filter)

    # Pagination (5 items per page)
    paginator = Paginator(attendance_records, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'users/attendance_list.html', {
        'page_obj': page_obj,
        'attendance_records': page_obj.object_list,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_count': paginator.count,
    })