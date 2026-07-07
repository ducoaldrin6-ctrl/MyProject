from django.urls import path
from . import views

app_name = 'security'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('webauthn/register/begin/', views.webauthn_register_begin, name='webauthn_register_begin'),
    path('webauthn/register/complete/', views.webauthn_register_complete, name='webauthn_register_complete'),
    path('webauthn/authenticate/begin/', views.webauthn_authenticate_begin, name='webauthn_authenticate_begin'),
    path('webauthn/authenticate/complete/', views.webauthn_authenticate_complete, name='webauthn_authenticate_complete'),
]