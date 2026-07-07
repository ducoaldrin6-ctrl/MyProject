from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('', views.application_list, name='list'),
    path('create/', views.application_create, name='create'),

    # dashboard counters / filters
    path('total/', views.total_applications, name='total'),
    path('approved/', views.approved_applications, name='approved'),
    path('pending/', views.pending_applications, name='pending'),
    path('rejected/', views.rejected_applications, name='rejected'),
    path('<int:id>/', views.application_detail, name='detail'),
path('<int:id>/edit/', views.application_edit, name='edit'),
]