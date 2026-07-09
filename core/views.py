import csv
import secrets
from datetime import timedelta
from functools import wraps
from io import BytesIO
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from .forms import ApplicationReviewForm, AttendanceForm, ApplicationForm, LoginForm, ScholarForm, SignUpForm, UserAccountForm
from .models import Application, AuditLog, AttendanceRecord, OTPCode, Scholar, User


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def log_action(request, user, action):
    AuditLog.objects.create(
        user=user,
        action=action,
        ip_address=get_client_ip(request),
    )


def generate_otp():
    return f"{secrets.randbelow(900000) + 100000}"


def send_otp(user, otp_code):
    if not user.email:
        return
    send_mail(
        subject='Your Richwell Scholarship login OTP',
        message=f'Your one-time password is {otp_code}. It expires in 5 minutes.',
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )


def issue_otp(request, user, action):
    otp_code = generate_otp()
    OTPCode.objects.create(user=user, code=otp_code)
    try:
        send_otp(user, otp_code)
        messages.success(request, 'OTP sent. Check your email for the code.')
    except Exception as exc:
        print(
            'OTP email failed: '
            f'{exc.__class__.__name__}: {exc}; '
            f'host={settings.EMAIL_HOST or "missing"}; '
            f'user_set={bool(settings.EMAIL_HOST_USER)}; '
            f'password_set={bool(settings.EMAIL_HOST_PASSWORD)}; '
            f'recipient_set={bool(user.email)}',
            flush=True,
        )
        print(f'OTP for {user.username}: {otp_code}', flush=True)
        if settings.OTP_SHOW_CODE_ON_EMAIL_FAILURE:
            messages.warning(request, f'Email is unavailable. Your OTP is {otp_code}.')
        else:
            messages.warning(request, 'OTP email could not be sent. Please contact an administrator or try again shortly.')
    log_action(request, user, action)


def login_attempt_key(request, username):
    username = (username or '').strip().lower() or 'unknown'
    return f"login_attempts:{get_client_ip(request)}:{username}"


def is_login_locked(request, username):
    return cache.get(login_attempt_key(request, username), 0) >= settings.LOGIN_MAX_ATTEMPTS


def record_failed_login(request, username):
    key = login_attempt_key(request, username)
    attempts = cache.get(key, 0) + 1
    cache.set(key, attempts, settings.LOGIN_LOCKOUT_SECONDS)


def reset_failed_login(request, username):
    cache.delete(login_attempt_key(request, username))


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if request.user.role != 'admin':
            return HttpResponseForbidden('You do not have permission to perform this action.')
        return view_func(request, *args, **kwargs)
    return wrapper


def excel_datetime(value):
    if not value:
        return ''
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.replace(tzinfo=None)


def get_scholar_queryset(query='', status_filter='', year_filter=''):
    scholars = Scholar.objects.select_related('assigned_to')
    if query:
        scholars = scholars.filter(
            Q(scholar_id__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(course__icontains=query)
        )
    if status_filter:
        scholars = scholars.filter(status=status_filter)
    if year_filter:
        scholars = scholars.filter(year_level=year_filter)
    return scholars


def get_attendance_queryset(query='', status_filter='', date_filter=''):
    attendance = AttendanceRecord.objects.select_related('scholar')
    if query:
        attendance = attendance.filter(
            Q(scholar__scholar_id__icontains=query) |
            Q(scholar__first_name__icontains=query) |
            Q(scholar__last_name__icontains=query)
        )
    if status_filter:
        attendance = attendance.filter(status=status_filter)
    if date_filter:
        attendance = attendance.filter(attendance_date=date_filter)
    return attendance


def get_application_queryset(query='', status_filter=''):
    applications = Application.objects.select_related('scholar', 'submitted_by', 'reviewed_by')
    if query:
        applications = applications.filter(
            Q(application_id__icontains=query) |
            Q(scholar__scholar_id__icontains=query) |
            Q(scholar__first_name__icontains=query) |
            Q(scholar__last_name__icontains=query)
        )
    if status_filter:
        applications = applications.filter(status=status_filter)
    return applications


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        username = request.POST.get('username', '')
        if is_login_locked(request, username):
            messages.error(request, 'Too many failed login attempts. Please wait before trying again.')
        elif form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                if user.is_active:
                    request.session['pre_auth_user'] = user.pk
                    reset_failed_login(request, username)
                    issue_otp(request, user, 'OTP generated for login')
                    return redirect('core:otp_verify')
                messages.error(request, 'Account is disabled.')
            else:
                record_failed_login(request, username)
                messages.error(request, 'Invalid username or password.')
        else:
            record_failed_login(request, username)
    return render(
        request,
        'core/login.html',
        {'form': form},
    )


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        messages.success(request, 'Account created. Log in to receive your OTP code.')
        log_action(request, user, 'Staff account created through signup')
        return redirect('core:login')

    return render(request, 'core/signup.html', {'form': form})


def otp_verify(request):
    user_id = request.session.get('pre_auth_user')
    if not user_id:
        return redirect('core:login')

    user = User.objects.filter(pk=user_id).first()
    if not user:
        return redirect('core:login')

    if request.method == 'POST':
        if request.POST.get('action') == 'resend':
            issue_otp(request, user, 'OTP resent for login')
            return redirect('core:otp_verify')

        otp_code = request.POST.get('otp_code')
        otp_record = OTPCode.objects.filter(user=user, code=otp_code, is_used=False).order_by('-created_at').first()
        if otp_record and timezone.now() - otp_record.created_at <= timedelta(seconds=settings.OTP_EXPIRATION_SECONDS):
            otp_record.is_used = True
            otp_record.save()
            login(request, user)
            del request.session['pre_auth_user']
            log_action(request, user, 'User logged in successfully via OTP')
            return redirect('core:dashboard')
        messages.error(request, 'Invalid or expired OTP, please try again.')
    return render(request, 'core/otp_verify.html', {'user': user})


@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        log_action(request, request.user, 'User logged out')
    logout(request)
    return redirect('core:login')


@login_required
def account_settings(request):
    return render(request, 'core/account_settings.html')


@login_required
def dashboard(request):
    scholar_count = Scholar.objects.count()
    attendance_count = AttendanceRecord.objects.count()
    application_count = Application.objects.count()
    application_total_commitment = Application.objects.aggregate(total=Sum('commitment_amount'))['total'] or 0
    application_pending_count = Application.objects.filter(status='pending').count()
    application_approved_count = Application.objects.filter(status='approved').count()
    application_rejected_count = Application.objects.filter(status='rejected').count()
    application_review_count = Application.objects.filter(status='under_review').count()
    scholar_active_count = Scholar.objects.filter(status='active').count()
    scholar_probation_count = Scholar.objects.filter(status='probation').count()
    scholar_inactive_count = Scholar.objects.filter(status='inactive').count()
    recent_applications = Application.objects.select_related('scholar').order_by('-submitted_at')[:5]
    stats = {
        'users_count': User.objects.count(),
        'active_otps': OTPCode.objects.filter(is_used=False).count(),
        'scholar_count': scholar_count,
        'attendance_count': attendance_count,
        'application_count': application_count,
        'application_total_commitment': application_total_commitment,
        'application_pending_count': application_pending_count,
        'application_approved_count': application_approved_count,
        'application_rejected_count': application_rejected_count,
        'application_review_count': application_review_count,
        'scholar_active_count': scholar_active_count,
        'scholar_probation_count': scholar_probation_count,
        'scholar_inactive_count': scholar_inactive_count,
    }
    return render(request, 'core/dashboard.html', {
        'stats': stats,
        'recent_applications': recent_applications,
    })


@login_required
def scholar_list(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    year_filter = request.GET.get('year_level', '')

    scholars = get_scholar_queryset(query, status_filter, year_filter)

    paginator = Paginator(scholars, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/scholar_list.html', {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'year_filter': year_filter,
        'status_choices': Scholar.SCHOLARSHIP_STATUS,
        'year_choices': Scholar.YEAR_LEVELS,
    })


@login_required
def scholar_detail(request, pk):
    scholar = get_object_or_404(Scholar, pk=pk)
    applications = scholar.applications.select_related('submitted_by', 'reviewed_by').order_by('-submitted_at')
    attendance_records = scholar.attendance_records.order_by('-attendance_date')[:10]
    return render(request, 'core/scholar_detail.html', {
        'scholar': scholar,
        'applications': applications,
        'attendance_records': attendance_records,
    })


@login_required
def scholar_create(request):
    if request.method == 'POST':
        form = ScholarForm(request.POST)
        if form.is_valid():
            scholar = form.save()
            log_action(request, request.user, f'Created scholar {scholar.scholar_id}')
            messages.success(request, 'Scholar created successfully.')
            return redirect('core:scholar_list')
    else:
        form = ScholarForm()
    return render(request, 'core/scholar_form.html', {'form': form, 'title': 'Add Scholar'})


@login_required
def scholar_update(request, pk):
    scholar = get_object_or_404(Scholar, pk=pk)
    if request.method == 'POST':
        form = ScholarForm(request.POST, instance=scholar)
        if form.is_valid():
            scholar = form.save()
            log_action(request, request.user, f'Updated scholar {scholar.scholar_id}')
            messages.success(request, 'Scholar updated successfully.')
            return redirect('core:scholar_list')
    else:
        form = ScholarForm(instance=scholar)
    return render(request, 'core/scholar_form.html', {'form': form, 'title': 'Edit Scholar'})


@login_required
@admin_required
def scholar_delete(request, pk):
    scholar = get_object_or_404(Scholar, pk=pk)
    if request.method == 'POST':
        scholar_id = scholar.scholar_id
        scholar.delete()
        log_action(request, request.user, f'Deleted scholar {scholar_id}')
        messages.success(request, 'Scholar deleted successfully.')
        return redirect('core:scholar_list')
    return render(request, 'core/scholar_confirm_delete.html', {'scholar': scholar})


@login_required
def attendance_list(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    attendance = get_attendance_queryset(query, status_filter, date_filter)

    paginator = Paginator(attendance, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/attendance_list.html', {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': AttendanceRecord.ATTENDANCE_STATUS,
    })


@login_required
def attendance_create(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save()
            log_action(request, request.user, f'Created attendance record {attendance.pk}')
            messages.success(request, 'Attendance record saved successfully.')
            return redirect('core:attendance_list')
    else:
        form = AttendanceForm()
    return render(request, 'core/attendance_form.html', {'form': form, 'title': 'Add Attendance'})


@login_required
def attendance_update(request, pk):
    attendance = get_object_or_404(AttendanceRecord, pk=pk)
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            attendance = form.save()
            log_action(request, request.user, f'Updated attendance record {attendance.pk}')
            messages.success(request, 'Attendance record updated successfully.')
            return redirect('core:attendance_list')
    else:
        form = AttendanceForm(instance=attendance)
    return render(request, 'core/attendance_form.html', {'form': form, 'title': 'Edit Attendance'})


@login_required
@admin_required
def attendance_delete(request, pk):
    attendance = get_object_or_404(AttendanceRecord, pk=pk)
    if request.method == 'POST':
        attendance_id = attendance.pk
        attendance.delete()
        log_action(request, request.user, f'Deleted attendance record {attendance_id}')
        messages.success(request, 'Attendance record deleted successfully.')
        return redirect('core:attendance_list')
    return render(request, 'core/attendance_confirm_delete.html', {'attendance': attendance})


@login_required
def attendance_export_csv(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    attendance = get_attendance_queryset(query, status_filter, date_filter).order_by('-attendance_date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Scholar ID', 'Scholar Name', 'Status', 'Notes'])
    for record in attendance:
        writer.writerow([
            record.attendance_date,
            record.scholar.scholar_id,
            f'{record.scholar.first_name} {record.scholar.last_name}',
            record.get_status_display(),
            record.notes,
        ])
    return response


@login_required
def attendance_export_excel(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    attendance = get_attendance_queryset(query, status_filter, date_filter).order_by('-attendance_date')

    try:
        from openpyxl import Workbook
    except ImportError:
        return HttpResponse('openpyxl is required for Excel export. Install the package and try again.', status=500)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Attendance Report'
    sheet.append(['Date', 'Scholar ID', 'Scholar Name', 'Status', 'Notes'])
    for record in attendance:
        sheet.append([
            record.attendance_date,
            record.scholar.scholar_id,
            f'{record.scholar.first_name} {record.scholar.last_name}',
            record.get_status_display(),
            record.notes,
        ])

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.xlsx"'
    return response


@login_required
def attendance_export_pdf(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    attendance = get_attendance_queryset(query, status_filter, date_filter).order_by('-attendance_date')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    x_left = inch * 0.5
    y = height - inch * 0.75

    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(x_left, y, 'Attendance Report')
    pdf.setFont('Helvetica', 9)
    y -= 18
    pdf.drawString(x_left, y, f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M")}')
    y -= 22

    headers = ['Date', 'Scholar ID', 'Scholar Name', 'Status', 'Notes']
    x_offsets = [0, 1.4 * inch, 3.6 * inch, 5.4 * inch, 6.6 * inch]
    pdf.setFont('Helvetica-Bold', 10)
    for header, offset in zip(headers, x_offsets):
        pdf.drawString(x_left + offset, y, header)
    y -= 14
    pdf.setFont('Helvetica', 9)

    for record in attendance:
        if y < inch:
            pdf.showPage()
            y = height - inch * 0.75
            pdf.setFont('Helvetica-Bold', 10)
            for header, offset in zip(headers, x_offsets):
                pdf.drawString(x_left + offset, y, header)
            y -= 14
            pdf.setFont('Helvetica', 9)

        pdf.drawString(x_left + x_offsets[0], y, str(record.attendance_date))
        pdf.drawString(x_left + x_offsets[1], y, record.scholar.scholar_id)
        pdf.drawString(x_left + x_offsets[2], y, f'{record.scholar.first_name} {record.scholar.last_name}')
        pdf.drawString(x_left + x_offsets[3], y, record.get_status_display())
        pdf.drawString(x_left + x_offsets[4], y, (record.notes or '')[:40])
        y -= 14

    pdf.save()
    return response


@login_required
def application_report(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    applications = get_application_queryset(query, status_filter).order_by('-submitted_at')

    totals = applications.aggregate(
        total_applications=Count('pk'),
        total_commitment=Sum('commitment_amount'),
        total_pending=Count('pk', filter=Q(status='pending')),
        total_under_review=Count('pk', filter=Q(status='under_review')),
        total_approved=Count('pk', filter=Q(status='approved')),
        total_rejected=Count('pk', filter=Q(status='rejected')),
    )
    totals.update({
        'total_scholars': Scholar.objects.count(),
        'active_scholars': Scholar.objects.filter(status='active').count(),
        'probation_scholars': Scholar.objects.filter(status='probation').count(),
        'inactive_scholars': Scholar.objects.filter(status='inactive').count(),
        'attendance_records': AttendanceRecord.objects.count(),
        'present_records': AttendanceRecord.objects.filter(status='present').count(),
        'late_records': AttendanceRecord.objects.filter(status='late').count(),
        'absent_records': AttendanceRecord.objects.filter(status='absent').count(),
        'excused_records': AttendanceRecord.objects.filter(status='excused').count(),
    })

    application_rows = applications[:50]

    return render(request, 'core/application_report.html', {
        'applications': application_rows,
        'totals': totals,
        'query': query,
        'status_filter': status_filter,
        'status_choices': Application.STATUS_CHOICES,
    })


@login_required
def application_report_pdf(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    applications = get_application_queryset(query, status_filter).order_by('-submitted_at')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="system_report.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    x_left = inch * 0.5
    y = height - inch * 0.75

    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(x_left, y, 'Overall System Application Report')
    pdf.setFont('Helvetica', 9)
    y -= 18
    pdf.drawString(x_left, y, f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M")}')
    if status_filter:
        pdf.drawString(x_left + 260, y, f'Status: {status_filter}')
    y -= 14
    if query:
        pdf.drawString(x_left, y, f'Search: {query}')
        y -= 14
    y -= 8

    header_cols = [
        ('App ID', 0),
        ('Scholar', 1.4 * inch),
        ('Status', 3.8 * inch),
        ('Amount', 5.4 * inch),
    ]

    pdf.setFont('Helvetica-Bold', 10)
    for text, offset in header_cols:
        pdf.drawString(x_left + offset, y, text)
    y -= 15
    pdf.setFont('Helvetica', 9)

    for application in applications:
        if y < inch:
            pdf.showPage()
            y = height - inch * 0.75
            pdf.setFont('Helvetica-Bold', 16)
            pdf.drawString(x_left, y, 'Overall System Application Report (continued)')
            y -= 22
            pdf.setFont('Helvetica-Bold', 10)
            for text, offset in header_cols:
                pdf.drawString(x_left + offset, y, text)
            y -= 15
            pdf.setFont('Helvetica', 9)

        pdf.drawString(x_left + header_cols[0][1], y, application.application_id)
        pdf.drawString(x_left + header_cols[1][1], y, f'{application.scholar.first_name} {application.scholar.last_name}')
        pdf.drawString(x_left + header_cols[2][1], y, application.get_status_display())
        pdf.drawString(x_left + header_cols[3][1], y, str(application.commitment_amount))
        y -= 14

    pdf.save()
    return response


@login_required
def application_detail_pdf(request, pk):
    application = get_object_or_404(Application, pk=pk)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="application_{application.application_id}.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    margin = inch * 0.5
    y = height - margin

    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(margin, y, f'Application {application.application_id}')
    y -= 22
    pdf.setFont('Helvetica', 10)
    pdf.drawString(margin, y, f'Scholar: {application.scholar}')
    y -= 16
    pdf.drawString(margin, y, f'Status: {application.get_status_display()}')
    y -= 16
    pdf.drawString(margin, y, f'Commitment Amount: {application.commitment_amount}')
    y -= 16
    pdf.drawString(margin, y, f'Submitted At: {application.submitted_at.strftime("%Y-%m-%d %H:%M")}')
    y -= 22

    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(margin, y, 'Parent / Guardian')
    y -= 18
    pdf.setFont('Helvetica', 10)
    pdf.drawString(margin, y, f'Parent: {application.parent_name} ({application.parent_relation})')
    y -= 14
    pdf.drawString(margin, y, f'Parent Phone: {application.parent_phone} | Email: {application.parent_email}')
    y -= 14
    pdf.drawString(margin, y, f'Guardian: {application.guardian_name or "N/A"} ({application.guardian_relation or "N/A"})')
    y -= 14
    pdf.drawString(margin, y, f'Guardian Phone: {application.guardian_phone or "N/A"} | Email: {application.guardian_email or "N/A"}')
    y -= 24

    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(margin, y, 'Notes & Remarks')
    y -= 18
    pdf.setFont('Helvetica', 10)
    text = application.student_notes or 'N/A'
    for line in text.splitlines():
        if y < margin + 40:
            pdf.showPage()
            y = height - margin
            pdf.setFont('Helvetica', 10)
        pdf.drawString(margin, y, line)
        y -= 14
    y -= 10
    text = application.remarks or 'N/A'
    for line in text.splitlines():
        if y < margin + 40:
            pdf.showPage()
            y = height - margin
            pdf.setFont('Helvetica', 10)
        pdf.drawString(margin, y, line)
        y -= 14

    pdf.save()
    return response


@login_required
def application_list(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    applications = get_application_queryset(query, status_filter)

    paginator = Paginator(applications, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/application_list.html', {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'status_choices': Application.STATUS_CHOICES,
    })


@login_required
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk)
    review_form = ApplicationReviewForm(instance=application)
    return render(request, 'core/application_detail.html', {'application': application, 'review_form': review_form})


@login_required
def application_create(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.submitted_by = request.user
            application.status = 'pending'
            application.save()
            log_action(request, request.user, f'Created application {application.application_id}')
            messages.success(request, 'Application submitted successfully.')
            return redirect('core:application_list')
    else:
        form = ApplicationForm()
    return render(request, 'core/application_form.html', {'form': form, 'title': 'New Application'})


@login_required
def application_update(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            application = form.save()
            log_action(request, request.user, f'Updated application {application.application_id}')
            messages.success(request, 'Application updated successfully.')
            return redirect('core:application_list')
    else:
        form = ApplicationForm(instance=application)
    return render(request, 'core/application_form.html', {'form': form, 'title': 'Edit Application'})


@login_required
@admin_required
@require_POST
def application_review(request, pk):
    application = get_object_or_404(Application, pk=pk)
    form = ApplicationReviewForm(request.POST, instance=application)
    if form.is_valid():
        application = form.save(commit=False)
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save()
        log_action(request, request.user, f'Reviewed application {application.application_id}: {application.status}')
        messages.success(request, 'Application review saved.')
    else:
        messages.error(request, 'Please correct the review form.')
    return redirect('core:application_detail', pk=application.pk)


@login_required
@admin_required
def application_delete(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        application_id = application.application_id
        application.delete()
        log_action(request, request.user, f'Deleted application {application_id}')
        messages.success(request, 'Application deleted successfully.')
        return redirect('core:application_list')
    return render(request, 'core/application_confirm_delete.html', {'application': application})


@login_required
def application_export_csv(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    applications = get_application_queryset(query, status_filter).order_by('-submitted_at')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="system_application_report.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Application ID',
        'Scholar ID',
        'Scholar Name',
        'Status',
        'Commitment Amount',
        'Submitted At',
        'Submitted By',
        'Reviewed By',
        'Reviewed At',
        'Parent Name',
        'Parent Phone',
        'Guardian Name',
        'Guardian Phone',
        'Remarks',
    ])

    for application in applications:
        writer.writerow([
            application.application_id,
            application.scholar.scholar_id,
            f'{application.scholar.first_name} {application.scholar.last_name}',
            application.get_status_display(),
            application.commitment_amount,
            excel_datetime(application.submitted_at),
            application.submitted_by or '',
            application.reviewed_by or '',
            excel_datetime(application.reviewed_at),
            application.parent_name,
            application.parent_phone,
            application.guardian_name,
            application.guardian_phone,
            application.remarks,
        ])
    return response


@login_required
def application_export_excel(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    applications = get_application_queryset(query, status_filter).order_by('-submitted_at')

    try:
        from openpyxl import Workbook
    except ImportError:
        return HttpResponse('openpyxl is required for Excel export. Install the package and try again.', status=500)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Application Report'
    sheet.append([
        'Application ID',
        'Scholar ID',
        'Scholar Name',
        'Status',
        'Commitment Amount',
        'Submitted At',
        'Submitted By',
        'Reviewed By',
        'Reviewed At',
        'Parent Name',
        'Parent Phone',
        'Guardian Name',
        'Guardian Phone',
        'Remarks',
    ])
    for application in applications:
        sheet.append([
            application.application_id,
            application.scholar.scholar_id,
            f'{application.scholar.first_name} {application.scholar.last_name}',
            application.get_status_display(),
            application.commitment_amount,
            excel_datetime(application.submitted_at),
            str(application.submitted_by or ''),
            str(application.reviewed_by or ''),
            excel_datetime(application.reviewed_at),
            application.parent_name,
            application.parent_phone,
            application.guardian_name,
            application.guardian_phone,
            application.remarks,
        ])

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="system_application_report.xlsx"'
    return response


@login_required
def application_export_pdf(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    applications = get_application_queryset(query, status_filter).order_by('-submitted_at')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="application_export.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    x_left = inch * 0.5
    y = height - inch * 0.75

    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(x_left, y, 'Application Export')
    pdf.setFont('Helvetica', 9)
    y -= 18
    pdf.drawString(x_left, y, f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M")}')
    if query:
        pdf.drawString(x_left + 260, y, f'Search: {query}')
    if status_filter:
        pdf.drawString(x_left + 430, y, f'Status: {status_filter}')
    y -= 14
    y -= 8

    header_cols = [
        ('App ID', 0),
        ('Scholar', 1.4 * inch),
        ('Status', 4.0 * inch),
        ('Amount', 5.6 * inch),
    ]

    pdf.setFont('Helvetica-Bold', 10)
    for text, offset in header_cols:
        pdf.drawString(x_left + offset, y, text)
    y -= 15
    pdf.setFont('Helvetica', 9)

    for application in applications:
        if y < inch:
            pdf.showPage()
            y = height - inch * 0.75
            pdf.setFont('Helvetica-Bold', 16)
            pdf.drawString(x_left, y, 'Application Export (continued)')
            y -= 22
            pdf.setFont('Helvetica-Bold', 10)
            for text, offset in header_cols:
                pdf.drawString(x_left + offset, y, text)
            y -= 15
            pdf.setFont('Helvetica', 9)

        pdf.drawString(x_left + header_cols[0][1], y, application.application_id)
        pdf.drawString(x_left + header_cols[1][1], y, f'{application.scholar.first_name} {application.scholar.last_name}')
        pdf.drawString(x_left + header_cols[2][1], y, application.get_status_display())
        pdf.drawString(x_left + header_cols[3][1], y, str(application.commitment_amount))
        y -= 14

    pdf.save()
    return response


@login_required
@admin_required
def audit_log_list(request):
    logs = AuditLog.objects.select_related('user').order_by('-created_at')
    paginator = Paginator(logs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/audit_log_list.html', {'page_obj': page_obj})


@login_required
@admin_required
def account_list(request):
    users = User.objects.order_by('username')
    return render(request, 'core/account_list.html', {'users': users})


@login_required
@admin_required
def account_create(request):
    if request.method == 'POST':
        form = UserAccountForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(request, request.user, f'Created account {user.username}')
            messages.success(request, 'Account created successfully.')
            return redirect('core:account_list')
    else:
        form = UserAccountForm()
    return render(request, 'core/account_form.html', {'form': form, 'title': 'Create Account'})


@login_required
@admin_required
def account_update(request, pk):
    account = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserAccountForm(request.POST, instance=account)
        if form.is_valid():
            user = form.save()
            log_action(request, request.user, f'Updated account {user.username}')
            messages.success(request, 'Account updated successfully.')
            return redirect('core:account_list')
    else:
        form = UserAccountForm(instance=account)
    return render(request, 'core/account_form.html', {'form': form, 'title': 'Edit Account'})
