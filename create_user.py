import os
import secrets

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scholarship_management.settings')
import django
django.setup()

from core.models import User

username = 'aldrin'
email = 'aldrin@example.com'
role = 'admin'

if User.objects.filter(username=username).exists():
    print(f"EXISTS: User '{username}' already exists")
else:
    password = secrets.token_urlsafe(12)
    user = User.objects.create_user(username=username, email=email, password=password)
    user.role = role
    if role == 'admin':
        user.is_staff = True
        user.is_superuser = True
    user.save()
    print('CREATED')
    print(f'username:{username}')
    print(f'email:{email}')
    print(f'password:{password}')
