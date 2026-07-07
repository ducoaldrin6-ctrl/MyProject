from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from applications.models import Application
from users.models import StudentProfile, Attendance


@login_required(login_url='/security/login/')
def dashboard_overview(request):
    """
    Display main dashboard with scholarship system statistics.
    Shows total applications, students, attendance records, and recent entries.
    """
    
    # Get statistics from database
    total_applications = Application.objects.count()
    total_students = StudentProfile.objects.count()
    total_attendance = Attendance.objects.count()
    
    # Get recent entries (last 5)
    recent_applications = Application.objects.select_related('user').order_by('-date_applied')[:5]
    recent_students = StudentProfile.objects.select_related('user').order_by('-user__date_joined')[:5]
    recent_attendance = Attendance.objects.select_related('user').order_by('-date')[:5]
    
    # Get application status breakdown
    pending_applications = Application.objects.filter(status='pending').count()
    approved_applications = Application.objects.filter(status='approved').count()
    rejected_applications = Application.objects.filter(status='rejected').count()
    
    # Prepare context
    context = {
        # Statistics
        'total_applications': total_applications,
        'total_students': total_students,
        'total_attendance': total_attendance,
        
        # Status breakdown
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        
        # Recent entries
        'recent_applications': recent_applications,
        'recent_students': recent_students,
        'recent_attendance': recent_attendance,
    }
    
    return render(request, 'dashboard/overview.html', context)


def stats_summary(request):
    """
    Return dashboard statistics for API or AJAX requests.
    Useful for real-time dashboard updates.
    """
    from django.http import JsonResponse
    
    stats = {
        'total_applications': Application.objects.count(),
        'total_students': StudentProfile.objects.count(),
        'total_attendance': Attendance.objects.count(),
        'pending_applications': Application.objects.filter(status='pending').count(),
        'approved_applications': Application.objects.filter(status='approved').count(),
        'rejected_applications': Application.objects.filter(status='rejected').count(),
    }
    
    return JsonResponse(stats)
