from django_rq import enqueue
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from auth_app.jobs import send_activation_email, send_password_reset_email
from auth_app.utils import (
    account_activation_token,
    build_activation_link,
    build_registration_response,
    get_user_from_uidb64,
    build_logo_url,
    build_password_reset_link,
    build_login_payload,
    set_auth_cookies,
    clear_auth_cookies,
    set_access_cookie,
)

from .serializers import RegisterSerializer, LoginSerializer, PasswordResetRequestSerializer

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return self._activate_and_respond(user, request)

    def _activate_and_respond(self, user, request):
        """Create the activation link, queue the email job, and return the response."""
        link, token = build_activation_link(user)
        logo_url = build_logo_url(request)
        enqueue(send_activation_email, user.id, link, logo_url)
        data = build_registration_response(user, token)
        return Response(data, status=status.HTTP_201_CREATED)


class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        user = get_user_from_uidb64(uidb64)
        if user is not None and account_activation_token.check_token(user, token):
            return self._activate_user(user)
        return Response(
            {"message": "Activation failed."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _activate_user(self, user):
        """Mark the user as active and persist the change."""
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response(
            {"message": "Account successfully activated."},
            status=status.HTTP_200_OK,
        )

    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return self._build_login_response(user)

    def _build_login_response(self, user):
        """Issue JWT tokens and attach them as HttpOnly cookies."""
        refresh = RefreshToken.for_user(user)
        response = Response(build_login_payload(user), status=status.HTTP_200_OK)
        return set_auth_cookies(response, str(refresh.access_token), str(refresh))


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response(
                {"detail": "Refresh token is missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._blacklist_and_respond(refresh_token)

    def _blacklist_and_respond(self, refresh_token):
        """Blacklist the refresh token and clear auth cookies."""
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass
        response = Response(
            {"detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."},
            status=status.HTTP_200_OK,
        )
        return clear_auth_cookies(response)


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response(
                {"detail": "Refresh token is missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._refresh_access_token(refresh_token)

    def _refresh_access_token(self, refresh_token):
        """Validate the refresh token and issue a new access token."""
        try:
            new_access = str(RefreshToken(refresh_token).access_token)
        except TokenError:
            return Response(
                {"detail": "Refresh token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        response = Response({"detail": "Token refreshed", "access": new_access}, status=status.HTTP_200_OK)
        return set_access_cookie(response, new_access)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._send_reset_email_if_user_exists(serializer.validated_data["email"], request)
        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK,
        )

    def _send_reset_email_if_user_exists(self, email, request):
        """Silently do nothing if no matching user is found (avoid account enumeration)."""
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            return
        link = build_password_reset_link(user)
        logo_url = build_logo_url(request)
        enqueue(send_password_reset_email, user.id, link, logo_url)