from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Application
from .forms import ApplicationForm


def application_list(request):
    # Get all applications as base queryset
    applications = Application.objects.all().order_by('-date_applied')

    # Search functionality (case-insensitive)
    search_query = request.GET.get('q', '').strip()
    if search_query:
        applications = applications.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(course__icontains=search_query) |
            Q(statement__icontains=search_query)
        )

    # Filter by status
    status_filter = request.GET.get('status', '').strip()
    if status_filter in ['pending', 'approved', 'rejected']:
        applications = applications.filter(status=status_filter)

    # Pagination (5 items per page)
    paginator = Paginator(applications, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'applications/list.html', {
        'page_obj': page_obj,
        'applications': page_obj.object_list,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_count': paginator.count,
    })


@login_required
def application_create(request):

    if request.method == 'POST':

        form = ApplicationForm(request.POST)

        if form.is_valid():

            application = form.save(commit=False)

            application.user = request.user

            application.save()

            messages.success(
                request,
                'Application submitted successfully!'
            )

            return redirect('applications:list')

        else:

            messages.error(
                request,
                'Please correct the errors below.'
            )

    else:

        form = ApplicationForm()

    return render(request, 'applications/create.html', {
        'form': form
    })


def total_applications(request):
    applications = Application.objects.all().order_by('-date_applied')

    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        applications = applications.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(course__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(applications, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'applications/list.html', {
        'page_obj': page_obj,
        'applications': page_obj.object_list,
        'title': 'All Applications',
        'search_query': search_query,
        'total_count': paginator.count,
    })


def approved_applications(request):
    applications = Application.objects.filter(status='approved').order_by('-date_applied')

    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        applications = applications.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(applications, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'applications/list.html', {
        'page_obj': page_obj,
        'applications': page_obj.object_list,
        'title': 'Approved Applications',
        'search_query': search_query,
        'status_filter': 'approved',
        'total_count': paginator.count,
    })


def pending_applications(request):
    applications = Application.objects.filter(status='pending').order_by('-date_applied')

    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        applications = applications.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(applications, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'applications/list.html', {
        'page_obj': page_obj,
        'applications': page_obj.object_list,
        'title': 'Pending Applications',
        'search_query': search_query,
        'status_filter': 'pending',
        'total_count': paginator.count,
    })


def rejected_applications(request):
    applications = Application.objects.filter(status='rejected').order_by('-date_applied')

    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        applications = applications.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(applications, 5)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'applications/list.html', {
        'page_obj': page_obj,
        'applications': page_obj.object_list,
        'title': 'Rejected Applications',
        'search_query': search_query,
        'status_filter': 'rejected',
        'total_count': paginator.count,
    })
def application_detail(request, id):
    application = Application.objects.get(id=id)

    return render(request, 'applications/detail.html', {
        'application': application
    })
def application_edit(request, id):
    application = Application.objects.get(id=id)

    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            return redirect('applications:list')
    else:
        form = ApplicationForm(instance=application)

    return render(request, 'applications/edit.html', {
        'form': form,
        'application': application
    })