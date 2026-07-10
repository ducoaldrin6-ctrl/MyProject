# Richwell Scholarship Management

A Django-based system for managing scholarship recipients, attendance records, application tracking, commitment fee reports, and exportable reports.

## Features

- Scholar CRUD with filtering and pagination
- Attendance tracking with CSV, Excel, and PDF exports
- Scholarship application tracking with staff submission and admin approval
- Commitment amount tracking for cashier payment reference
- OTP-based login flow using Django email backend
- Admin-only delete permissions
- Admin account management and audit trail screens
- Audit logs for login, create, update, and delete actions
- Demo data seeding for quick presentation setup
- Basic automated tests for permissions, validation, and page rendering
- Explainable student-support risk insights using local attendance and application data

## Requirements

- Python 3.14 or compatible Python 3 version
- Django and dependencies from `requirements.txt`

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Apply migrations:

```powershell
python manage.py migrate
```

Create an admin user:

```powershell
python manage.py createsuperuser
```

Run the server:

```powershell
python manage.py runserver
```

If your terminal is not using the virtual environment, run the project with the venv Python directly:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

## Demo Data

Create demo users, scholars, attendance, and applications:

```powershell
python manage.py seed_demo
```

Demo logins:

- Admin: `admin_demo` / `AdminDemo123!`
- Staff: `staff_demo` / `StaffDemo123!`

The command is idempotent, so it is safe to run more than once.

## Workflow

- Staff can create and update scholar applications.
- Applications start as `Pending`.
- Admin users review applications and set them to `Approved`, `Rejected`, or `Under Review`.
- `Commitment Amount` is only the amount the scholar should pay at the cashier. It is not tracked as paid/unpaid inside this system.
- Admin users can manage user accounts and view audit trails.
- The Insights screen prioritizes possible follow-ups; it never approves, rejects, or changes a scholarship.

## Machine Learning

The support model estimates retention follow-up risk from absence rate, lateness, attendance history, rejected-application rate, and year level. With at least 20 scholars and at least 5 examples in both active and concern groups, it trains a balanced logistic-regression model on the local database. Smaller datasets use a transparent baseline so the screen remains useful without pretending that limited data is a reliable trained model.

Every result includes its contributing factors, a confidence level, and a suggested human action. Personal scholar data stays inside the application and is not sent to an external AI API. The result is decision support only and must not be used to automatically determine scholarship eligibility.

## Configuration

Optional environment variables:

- `DJANGO_SECRET_KEY`: production secret key
- `DJANGO_DEBUG`: `True` or `False`
- `DJANGO_ALLOWED_HOSTS`: comma-separated allowed hosts
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma-separated trusted HTTPS origins, for example `https://your-domain.com`
- `RECAPTCHA_SITE_KEY`: Google reCAPTCHA site key
- `RECAPTCHA_SECRET_KEY`: Google reCAPTCHA secret key
- `LOGIN_MAX_ATTEMPTS`: failed login attempts before temporary lockout
- `LOGIN_LOCKOUT_SECONDS`: lockout duration in seconds
- `DATABASE_URL`: PostgreSQL connection URL; the Render blueprint configures this automatically

For local development, OTP emails are printed to the console because the project uses Django's console email backend.

Use `.env.example` as a guide for production hosting variables. Do not commit your real `.env` file.

## OTP Email Setup

For local development, OTP codes print in the terminal where `runserver` is running.

For Gmail SMTP:

1. Enable 2-Step Verification on your Google account.
2. Create a Gmail App Password from your Google Account security settings.
3. Set these environment variables on your hosting provider:

```powershell
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=yourgmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=yourgmail@gmail.com
```

Do not use your normal Gmail password. Gmail requires an App Password.

Free/low-cost SMTP alternatives:

- Brevo SMTP
- Mailersend SMTP
- Mailgun SMTP trial
- SendGrid SMTP free tier, if available in your region

Use the SMTP host, port, username, and password they provide with the same `EMAIL_*` variables.

Brevo mapping:

- Brevo SMTP Server -> `EMAIL_HOST`
- Brevo Port -> `EMAIL_PORT`
- Brevo Login -> `EMAIL_HOST_USER`
- Brevo SMTP Key, usually starts with `xsmtpsib-` -> `EMAIL_HOST_PASSWORD`
- Your verified sender email in Brevo -> `DEFAULT_FROM_EMAIL`

Brevo API keys that start with `xkeysib-` are not needed for this Django SMTP setup.

## reCAPTCHA Setup

The login page supports Google reCAPTCHA v2 checkbox.

1. Go to `https://www.google.com/recaptcha/admin`.
2. Create a reCAPTCHA v2 Checkbox site.
3. Add your local/production domains.
4. Set `RECAPTCHA_SITE_KEY` and `RECAPTCHA_SECRET_KEY` in your environment.

In local development on `localhost` or `127.0.0.1`, reCAPTCHA is bypassed when `DJANGO_DEBUG=True`. In production, set `DJANGO_DEBUG=False` so captcha is required.

## Hosting Checklist

- Set `DJANGO_DEBUG=False`.
- Set a strong `DJANGO_SECRET_KEY`.
- Set `DJANGO_ALLOWED_HOSTS` to your domain.
- Set `DJANGO_CSRF_TRUSTED_ORIGINS` to your `https://` domain.
- Configure SMTP email for OTP delivery.
- Configure reCAPTCHA keys.
- Run `python manage.py collectstatic`.
- Run `python manage.py migrate`.

## Tests

Run the test suite:

```powershell
python manage.py test
```

Run Django system checks:

```powershell
python manage.py check
```
