from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('security:login')),

    path('dashboard/', include('dashboard.urls')),
    path('security/', include('security.urls')),

    path('users/', include('users.urls')),
    path('applications/', include('applications.urls')),
    # API endpoints
    path('api/', include('store.urls')),

    path('admin/', admin.site.urls),
]
