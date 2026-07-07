from django.conf import settings
from django.core.mail import send_mail

from .utils import render_activation_email


def send_activation_email(user_id, activation_link, logo_url):
    """RQ job: sends the activation email asynchronously in the background."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    html_message, plain_message = render_activation_email(user, activation_link, logo_url)
    send_mail(
        subject="Please confirm your email address",
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

def send_password_reset_email(user_id, reset_link, logo_url):
    """RQ job: sends the password reset email asynchronously in the background."""
    from django.contrib.auth import get_user_model
    from .utils import render_password_reset_email

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    html_message, plain_message = render_password_reset_email(user, reset_link, logo_url)
    send_mail(
        subject="Reset your password",
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )