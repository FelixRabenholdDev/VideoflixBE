from django_rq import enqueue
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.jobs import send_activation_email
from auth_app.utils import (
    build_activation_link,
    build_registration_response,
    create_verification_token,
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
        verification = create_verification_token(user)
        link = build_activation_link(user.id, verification.token)
        enqueue(send_activation_email, user.id, link)
        data = build_registration_response(user, verification.token)
        return Response(data, status=status.HTTP_201_CREATED)