from django.conf import settings
from django.core.mail import send_mail

from .utils import render_activation_email


def send_activation_email(user_id, activation_link):
    """RQ-Job: versendet die Aktivierungs-E-Mail asynchron."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    html_message, plain_message = render_activation_email(user, activation_link)
    send_mail(
        subject="Bitte bestätige deine E-Mail-Adresse",
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )