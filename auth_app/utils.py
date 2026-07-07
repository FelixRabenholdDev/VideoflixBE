from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import EmailVerificationToken


def create_verification_token(user):
    """Erstellt ein neues Aktivierungs-Token für den User."""
    return EmailVerificationToken.objects.create(user=user)


def build_activation_link(user_id, token):
    """Baut den Link zur Frontend-Aktivierungsseite."""
    return f"{settings.FRONTEND_URL}/activate/{user_id}/{token}/"


def render_activation_email(user, activation_link):
    """Rendert HTML- und Text-Version der Aktivierungs-Mail."""
    context = {"user": user, "activation_link": activation_link}
    html_message = render_to_string("emails/verify_email.html", context)
    plain_message = strip_tags(html_message)
    return html_message, plain_message


def build_registration_response(user, token):
    """Baut die Response-Daten für die erfolgreiche Registrierung."""
    return {
        "user": {"id": user.id, "email": user.email},
        "token": str(token),
    }