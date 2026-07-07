from django_rq import enqueue
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.jobs import send_activation_email
from auth_app.utils import (
    account_activation_token,
    build_activation_link,
    build_registration_response,
    get_user_from_uidb64,
    build_logo_url,
    build_login_payload,
    set_auth_cookies,
)

from .serializers import RegisterSerializer, LoginSerializer


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