from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """Reads the JWT access token from the HttpOnly cookie instead of the Authorization header."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
    
    def _validate_or_ignore(self, raw_token):
        """Return the authenticated user, or None if the token is invalid/expired
        (invalid tokens are treated as 'not authenticated' rather than an error,
        so public endpoints keep working even with a stale cookie present)."""
        try:
            validated_token = self.get_validated_token(raw_token)
        except (InvalidToken, TokenError):
            return None
        return self.get_user(validated_token), validated_token