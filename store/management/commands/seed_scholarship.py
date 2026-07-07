from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from applications.models import Application
from users.models import StudentProfile, Attendance
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed sample scholarship data: users, student profiles, applications, attendance'

    def handle(self, *args, **options):
        created = 0

        # create users
        users_data = [
            {'username': 'student1', 'first_name': 'Alice', 'last_name': 'Garcia', 'email': 'alice@example.com', 'password': 'pass'},
            {'username': 'student2', 'first_name': 'Bob', 'last_name': 'Reyes', 'email': 'bob@example.com', 'password': 'pass'},
        ]

        users = []
        for u in users_data:
            user, created_user = User.objects.get_or_create(username=u['username'], defaults={
                'first_name': u['first_name'],
                'last_name': u['last_name'],
                'email': u['email'],
            })
            if created_user:
                user.set_password(u['password'])
                user.save()
                created += 1
            users.append(user)

        # create student profiles
        for user in users:
            profile, prof_created = StudentProfile.objects.get_or_create(user=user, defaults={
                'course': 'BS Computer Science',
                'year_level': '2',
                'contact_number': '09171234567',
                'address': '123 Student St.'
            })
            if prof_created:
                created += 1

        # create applications
        for i, user in enumerate(users, start=1):
            app, app_created = Application.objects.get_or_create(
                user=user,
                full_name=f"{user.first_name} {user.last_name}",
                defaults={
                    'email': user.email,
                    'course': 'BS Computer Science',
                    'year_level': '2',
                    'commitment': 'Full-time',
                    'statement': f'I am applying for scholarship (sample {i}).',
                    'status': 'pending',
                }
            )
            if app_created:
                created += 1

        # create attendance records
        today = timezone.now().date()
        for user in users:
            att, att_created = Attendance.objects.get_or_create(user=user, date=today, defaults={
                'status': 'present',
                'notes': 'Seeded attendance'
            })
            if att_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Seeding complete. Created/updated {created} records.'))