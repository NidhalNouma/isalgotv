from urllib.parse import urlparse

from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.cache import cache
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.views.decorators.http import require_http_methods

from profile_user.models import User_Profile
from profile_user.tasks import send_welcome_email_task
from profile_user.utils.send_mails import send_verification_email
from auth.forms import UserCreationEmailForm

VERIFY_SALT = 'email-verification'
VERIFY_MAX_AGE = 60 * 60 * 24 * 3


def _is_safe_redirect(url):
    """Allow relative paths and full URLs on trusted subdomains."""
    if url and url.startswith('/'):
        return True
    try:
        parsed = urlparse(url)
        parent = getattr(settings, 'PARENT_HOST', '')
        if parent and parsed.hostname and parsed.hostname.endswith('.' + parent):
            return True
    except Exception:
        pass
    return False


def _send_verification(request, user):
    token = signing.dumps({'uid': user.pk, 'email': user.email}, salt=VERIFY_SALT)
    url = request.build_absolute_uri(reverse('verify_email', args=[token]))
    profile = User_Profile.objects.filter(user=user).first()
    language = (profile.language if profile and profile.language else 'en')
    return send_verification_email(user.email, url, language)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationEmailForm(request.POST) 
        try:
            if form.is_valid():
                user = form.save(commit=False)
                user.email = user.username
                user.save()
                User_Profile.objects.create(user = user, email_verified=False)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                _send_verification(request, user)
                messages.info(request, _("We sent a confirmation link to %(email)s. Please check your inbox.") % {'email': user.email})

                next_url = request.POST.get('next', '')
                if next_url and _is_safe_redirect(next_url):
                    return redirect(next_url)
                return redirect('index')
            else:
                messages.error(request, _("An error occurred while registering"))

        except Exception as e:
            print("An error occurred while registering", e)
            messages.error(request, _("An error occurred while registering"))

    return render(request,'auth/register.html', {'form': form})

def verify_email(request, token):
    try:
        data = signing.loads(token, salt=VERIFY_SALT, max_age=VERIFY_MAX_AGE)
        user = User.objects.get(pk=data['uid'], email=data['email'])
    except signing.SignatureExpired:
        messages.error(request, _("This confirmation link has expired. Please request a new one."))
        return redirect('index')
    except (signing.BadSignature, User.DoesNotExist, KeyError):
        messages.error(request, _("Invalid confirmation link."))
        return redirect('index')

    profile, _created = User_Profile.objects.get_or_create(user=user)
    if not profile.email_verified:
        profile.email_verified = True
        profile.save(update_fields=['email_verified'])
        send_welcome_email_task(user.email, user.email, profile.language or 'en')
    messages.success(request, _("Your email has been confirmed. Thank you!"))
    return redirect('index')


@login_required(login_url='login')
def verify_required(request):
    profile = getattr(request, 'user_profile', None)
    if profile is None or profile.email_verified:
        return redirect('index')
    return render(request, 'auth/verify_required.html', {'email': request.user.email})


@require_http_methods(["POST"])
@login_required(login_url='login')
def resend_verification_email(request):
    profile = User_Profile.objects.filter(user=request.user).first()
    if profile and profile.email_verified:
        messages.info(request, _("Your email is already confirmed."))
    elif cache.add(f'verify_email_resend_{request.user.pk}', 1, 60):
        _send_verification(request, request.user)
        messages.info(request, _("A new confirmation link has been sent."))
    else:
        messages.error(request, _("Please wait a minute before requesting another email."))
    return redirect('verify_required')


def logout_user(request):
    logout(request)

    # Clear any stored messages
    storage = messages.get_messages(request)
    for _ in storage:
        pass 

    referer_url = request.META.get('HTTP_REFERER')
    # Returning to the verify page would bounce a logged-out user to a login redirect
    if referer_url and 'verify-required' not in referer_url:
        return redirect(referer_url)
    return redirect('index')

def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username = email)
        except Exception as e:
            messages.error(request, _("User does not exist!"))
            return render(request, 'auth/login.html')

        user = authenticate(request, username = email, password = password)
        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            next_url = request.POST.get('next', '')
            if next_url and _is_safe_redirect(next_url):
                return redirect(next_url)
            return redirect('index')
        else:
            messages.error(request, _("Email or Password incorrect!"))

    return render(request, 'auth/login.html')

@require_http_methods([ "POST"])
def update_user_password(request):
    if request.user.is_authenticated:
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return render(request, 'include/settings/password.html', {'msg': _('Password updated succesfully!')})

        return render(request, 'include/settings/password.html', {'form': form})
