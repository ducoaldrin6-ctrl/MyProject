from datetime import date
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Application, AttendanceRecord, AuditLog, Scholar, User


class CoreViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            password='password123',
            role='admin',
            is_staff=True,
            is_superuser=True,
        )
        self.staff = User.objects.create_user(
            username='staff',
            password='password123',
            role='staff',
        )
        self.scholar = Scholar.objects.create(
            scholar_id='SCH-001',
            first_name='Ana',
            last_name='Santos',
            date_of_birth=date(2004, 1, 1),
            sex='female',
            address='Test Address',
            email='ana@example.com',
            phone='09170000000',
            course='BS Information Technology',
            year_level='1',
            status='active',
        )

    def test_authenticated_pages_render(self):
        self.client.force_login(self.staff)

        urls = [
            reverse('core:dashboard'),
            reverse('core:scholar_list'),
            reverse('core:attendance_list'),
            reverse('core:application_list'),
            reverse('core:application_report'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_signup_page_renders_for_guests(self):
        response = self.client.get(reverse('core:signup'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Staff Account')

    def test_signup_creates_staff_account(self):
        response = self.client.post(reverse('core:signup'), {
            'username': 'newstaff',
            'email': 'newstaff@example.com',
            'first_name': 'New',
            'last_name': 'Staff',
            'password1': 'StrongPass2026!',
            'password2': 'StrongPass2026!',
        })

        self.assertRedirects(response, reverse('core:login'))
        user = User.objects.get(username='newstaff')
        self.assertEqual(user.role, 'staff')
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password('StrongPass2026!'))

    def test_authenticated_user_cannot_open_signup(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('core:signup'))

        self.assertRedirects(response, reverse('core:dashboard'))

    def test_staff_cannot_delete_scholar(self):
        self.client.force_login(self.staff)

        response = self.client.post(reverse('core:scholar_delete', args=[self.scholar.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Scholar.objects.filter(pk=self.scholar.pk).exists())

    def test_admin_can_delete_scholar(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse('core:scholar_delete', args=[self.scholar.pk]))

        self.assertRedirects(response, reverse('core:scholar_list'))
        self.assertFalse(Scholar.objects.filter(pk=self.scholar.pk).exists())
        self.assertTrue(AuditLog.objects.filter(action__contains='Deleted scholar SCH-001').exists())

    def test_scholar_create_writes_audit_log(self):
        self.client.force_login(self.staff)

        response = self.client.post(reverse('core:scholar_create'), {
            'scholar_id': 'SCH-002',
            'first_name': 'Ben',
            'last_name': 'Reyes',
            'date_of_birth': '2003-05-15',
            'sex': 'male',
            'address': 'Sample Address',
            'email': 'ben@example.com',
            'phone': '09171111111',
            'course': 'BS Accountancy',
            'year_level': '2',
            'status': 'active',
            'assigned_to': '',
            'date_enrolled': '2026-01-01',
        })

        self.assertRedirects(response, reverse('core:scholar_list'))
        self.assertTrue(Scholar.objects.filter(scholar_id='SCH-002').exists())
        self.assertTrue(AuditLog.objects.filter(action__contains='Created scholar SCH-002').exists())

    def test_form_rejects_future_attendance_date(self):
        self.client.force_login(self.staff)

        response = self.client.post(reverse('core:attendance_create'), {
            'scholar': self.scholar.pk,
            'attendance_date': '2999-01-01',
            'status': 'present',
            'notes': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(AttendanceRecord.objects.exists())
        self.assertContains(response, 'Attendance date cannot be in the future.')

    def test_application_create_writes_pending_application(self):
        self.client.force_login(self.staff)

        response = self.client.post(reverse('core:application_create'), {
            'scholar': self.scholar.pk,
            'application_id': 'APP-001',
            'student_notes': '',
            'parent_name': 'Maria Santos',
            'parent_relation': 'Mother',
            'parent_phone': '09172222222',
            'parent_email': 'maria@example.com',
            'guardian_name': '',
            'guardian_relation': '',
            'guardian_phone': '',
            'guardian_email': '',
            'commitment_amount': '1000.00',
            'remarks': '',
        })

        self.assertRedirects(response, reverse('core:application_list'))
        application = Application.objects.get(application_id='APP-001')
        self.assertEqual(application.status, 'pending')
        self.assertEqual(application.submitted_by, self.staff)

    def test_staff_cannot_delete_application(self):
        application = Application.objects.create(
            scholar=self.scholar,
            application_id='APP-002',
            parent_name='Maria Santos',
            parent_relation='Mother',
            parent_phone='09172222222',
            parent_email='maria@example.com',
            commitment_amount='1000.00',
            status='pending',
        )
        self.client.force_login(self.staff)

        response = self.client.post(reverse('core:application_delete', args=[application.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Application.objects.filter(pk=application.pk).exists())

    def test_attendance_csv_export_uses_filters(self):
        AttendanceRecord.objects.create(
            scholar=self.scholar,
            attendance_date=date(2026, 1, 1),
            status='present',
            notes='Included row',
        )
        self.client.force_login(self.staff)

        response = self.client.get(reverse('core:attendance_export_csv'), {'q': 'SCH-001'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Included row')
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_seed_demo_command_is_idempotent(self):
        output = StringIO()
        call_command('seed_demo', stdout=output, verbosity=0)
        call_command('seed_demo', stdout=output, verbosity=0)

        self.assertTrue(User.objects.filter(username='admin_demo', role='admin').exists())
        self.assertTrue(User.objects.filter(username='staff_demo', role='staff').exists())
        self.assertEqual(Scholar.objects.filter(scholar_id__startswith='SCH-100').count(), 3)
        self.assertEqual(Application.objects.filter(application_id__startswith='APP-2026').count(), 3)

    def test_admin_can_review_application(self):
        application = Application.objects.create(
            scholar=self.scholar,
            application_id='APP-003',
            parent_name='Maria Santos',
            parent_relation='Mother',
            parent_phone='09172222222',
            parent_email='maria@example.com',
            commitment_amount='1000.00',
            status='pending',
        )
        self.client.force_login(self.admin)

        response = self.client.post(reverse('core:application_review', args=[application.pk]), {
            'status': 'approved',
            'remarks': 'Approved for cashier processing.',
        })

        self.assertRedirects(response, reverse('core:application_detail', args=[application.pk]))
        application.refresh_from_db()
        self.assertEqual(application.status, 'approved')
        self.assertEqual(application.reviewed_by, self.admin)
        self.assertIsNotNone(application.reviewed_at)

    def test_staff_cannot_access_admin_account_and_audit_pages(self):
        self.client.force_login(self.staff)

        self.assertEqual(self.client.get(reverse('core:account_list')).status_code, 403)
        self.assertEqual(self.client.get(reverse('core:audit_log_list')).status_code, 403)

    def test_account_settings_shows_role_limited_access(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('core:account_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff accounts can use daily scholarship workflows')

    def test_account_settings_shows_admin_controls(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('core:account_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage Accounts')
        self.assertContains(response, 'View Audit Logs')
