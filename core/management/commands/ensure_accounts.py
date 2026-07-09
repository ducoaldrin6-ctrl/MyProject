import os

from django.core.management.base import BaseCommand

from core.models import User


class Command(BaseCommand):
    help = 'Create default admin and staff accounts from environment variables.'

    def handle(self, *args, **options):
        accounts = [
            {
                'username': os.environ.get('ADMIN_USERNAME'),
                'password': os.environ.get('ADMIN_PASSWORD'),
                'email': os.environ.get('ADMIN_EMAIL', ''),
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': os.environ.get('STAFF_USERNAME'),
                'password': os.environ.get('STAFF_PASSWORD'),
                'email': os.environ.get('STAFF_EMAIL', ''),
                'role': 'staff',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        for account in accounts:
            username = account['username']
            password = account['password']
            if not username or not password:
                continue

            user, created = User.objects.get_or_create(username=username)
            user.email = account['email']
            user.role = account['role']
            user.is_staff = account['is_staff']
            user.is_superuser = account['is_superuser']
            user.set_password(password)
            user.save()

            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} {account["role"]} account: {username}'))
