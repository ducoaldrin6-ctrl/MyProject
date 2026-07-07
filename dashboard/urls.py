from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_overview, name='overview'),
    path('stats/', views.stats_summary, name='stats_summary'),
]
