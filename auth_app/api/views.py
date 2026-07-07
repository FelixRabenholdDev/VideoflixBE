from django_rq import enqueue
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.jobs import send_activation_email
from auth_app.utils import (
    account_activation_token,
    build_activation_link,
    build_registration_response,
    get_user_from_uidb64,
)

from .serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return self._activate_and_respond(user)

    def _activate_and_respond(self, user):
        """Create the activation link, queue the email job, and return the response."""
        link, token = build_activation_link(user)
        enqueue(send_activation_email, user.id, link)
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