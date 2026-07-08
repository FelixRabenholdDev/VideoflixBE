from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.templatetags.static import static

User = get_user_model()


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Token becomes invalid once the user is activated (is_active flips to True)."""

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_active}"


account_activation_token = AccountActivationTokenGenerator()

def build_logo_url(request):
    """Build the absolute URL to the Videoflix logo for use in emails."""
    return request.build_absolute_uri(static("emails/logo.svg"))


def build_activation_link(user):
    """Build the activation link containing uidb64 and token."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    return f"{settings.FRONTEND_URL}/activate/{uidb64}/{token}/", token


def get_user_from_uidb64(uidb64):
    """Decode uidb64 and return the matching user, or None if invalid."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def render_activation_email(user, activation_link, logo_url):
    """Render the HTML and plain text versions of the activation email."""
    context = {"user": user, "activation_link": activation_link, "frontend_url": settings.FRONTEND_URL, "logo_url": logo_url,}
    html_message = render_to_string("emails/verify_email.html", context)
    plain_message = strip_tags(html_message)
    return html_message, plain_message


def build_registration_response(user, token):
    """Build the response payload for a successful registration."""
    return {
        "user": {"id": user.id, "email": user.email},
        "token": token,
    }

def build_password_reset_link(user):
    """Build the password reset link containing uidb64 and token."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/"


def render_password_reset_email(user, reset_link, logo_url):
    """Render the HTML and plain text versions of the password reset email."""
    context = {"reset_link": reset_link, "logo_url": logo_url}
    html_message = render_to_string("emails/password_reset.html", context)
    plain_message = strip_tags(html_message)
    return html_message, plain_message

def set_auth_cookies(response, access_token, refresh_token):
    """Attach the JWT access and refresh tokens as HttpOnly cookies."""
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
    )
    return response


def build_login_payload(user):
    """Build the response payload for a successful login."""
    return {
        "detail": "Login successful",
        "user": {"id": user.id, "username": user.email},
    }

def clear_auth_cookies(response):
    """Remove the access and refresh token cookies from the response."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

def set_access_cookie(response, access_token):
    """Attach only the new JWT access token as an HttpOnly cookie."""
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
    )
    return response