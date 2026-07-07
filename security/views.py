import json
import os
from urllib import parse, request as urllib_request

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm
from .models import WebAuthnCredential

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
)
import webauthn.helpers.exceptions as webauthn_exceptions


def verify_recaptcha(response_token):
    # In development mode, skip reCAPTCHA verification
    if getattr(settings, 'DEBUG', False):
        if response_token:  # Just require that a response was submitted
            return True, []
        return False, ['missing-input-response']
    
    secret_key = getattr(settings, 'GOOGLE_RECAPTCHA_SECRET_KEY', None)
    if not secret_key:
        return False, ['recaptcha-secret-key-missing']

    if not response_token:
        return False, ['missing-input-response']

    data = parse.urlencode({
        'secret': secret_key,
        'response': response_token,
    }).encode('utf-8')

    req = urllib_request.Request(
        'https://www.google.com/recaptcha/api/siteverify',
        data=data,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    )

    try:
        with urllib_request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
    except Exception:
        return False, ['recaptcha-verification-failed']

    return result.get('success', False), result.get('error-codes', [])


def login_view(request):
    form = LoginForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            recaptcha_token = request.POST.get('g-recaptcha-response', '')
            recaptcha_valid, recaptcha_errors = verify_recaptcha(recaptcha_token)

            if not recaptcha_valid:
                messages.error(request, 'reCAPTCHA verification failed. Please complete the challenge.')
            else:
                # Email authentication logic
                identifier = form.cleaned_data['username_or_email']
                password = form.cleaned_data['password']

                # Try to find user by email first, otherwise assume username
                from django.contrib.auth.models import User
                try:
                    if '@' in identifier:
                        user_obj = User.objects.get(email=identifier)
                        username = user_obj.username
                    else:
                        username = identifier
                except User.DoesNotExist:
                    username = identifier # Let authenticate handle failure

                user = authenticate(request, username=username, password=password)

                if user is not None:
                    login(request, user)
                    return redirect('users:dashboard')
                else:
                    messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'login.html', {
        'form': form,
        'recaptcha_site_key': getattr(settings, 'GOOGLE_RECAPTCHA_SITE_KEY', ''),
    })


def logout_view(request):
    logout(request)
    return redirect('security:login')


def get_origin(request):
    protocol = 'https://' if request.is_secure() else 'http://'
    return protocol + request.get_host()


@login_required
def webauthn_register_begin(request):
    challenge = os.urandom(64)
    request.session['webauthn_challenge'] = challenge.hex()

    options = generate_registration_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_name=request.user.username,
        user_display_name=request.user.get_full_name() or request.user.username,
        challenge=challenge,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    request.session['webauthn_registration_user_id'] = options.user.id.hex()
    request.session['webauthn_registration_challenge'] = challenge.hex()
    return JsonResponse({'options': json.loads(options_to_json(options))})


@login_required
def webauthn_register_complete(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    challenge_hex = request.session.pop('webauthn_registration_challenge', None)
    if not challenge_hex:
        return JsonResponse({'error': 'No challenge found. Start registration again.'}, status=400)

    try:
        verification = verify_registration_response(
            credential=body,
            expected_challenge=bytes.fromhex(challenge_hex),
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=get_origin(request),
        )
    except webauthn_exceptions.RegistrationError as e:
        return JsonResponse({'error': f'Verification failed: {str(e)}'}, status=400)

    credential_id = verification.credential_id.hex()
    if WebAuthnCredential.objects.filter(credential_id=credential_id).exists():
        return JsonResponse({'error': 'Credential already registered'}, status=409)

    WebAuthnCredential.objects.create(
        user=request.user,
        credential_id=credential_id,
        public_key=verification.credential_public_key.hex(),
        sign_count=verification.sign_count,
    )

    return JsonResponse({'success': True, 'credential_id': credential_id})


def webauthn_authenticate_begin(request):
    challenge = os.urandom(64)
    request.session['webauthn_auth_challenge'] = challenge.hex()
    request.session['webauthn_auth_username'] = ''

    options = generate_authentication_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        challenge=challenge,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    return JsonResponse({'options': json.loads(options_to_json(options))})


def webauthn_authenticate_complete(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    challenge_hex = request.session.pop('webauthn_auth_challenge', None)
    if not challenge_hex:
        return JsonResponse({'error': 'No challenge found. Start authentication again.'}, status=400)

    credential_id_str = body.get('id', '')
    try:
        cred = WebAuthnCredential.objects.get(credential_id=credential_id_str)
    except WebAuthnCredential.DoesNotExist:
        return JsonResponse({'error': 'Credential not found'}, status=404)

    try:
        verification = verify_authentication_response(
            credential=body,
            expected_challenge=bytes.fromhex(challenge_hex),
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=get_origin(request),
            credential_public_key=bytes.fromhex(cred.public_key),
            credential_current_sign_count=cred.sign_count,
            require_user_verification=False,
        )
    except webauthn_exceptions.AuthenticationError as e:
        return JsonResponse({'error': f'Verification failed: {str(e)}'}, status=400)

    cred.sign_count = verification.new_sign_count
    cred.save(update_fields=['sign_count'])

    user = cred.user
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    return JsonResponse({'success': True, 'username': user.username})