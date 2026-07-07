from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


GENERIC_ERROR = "Please check your input and try again."


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "password", "confirmed_password"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        """Reject duplicate emails without revealing that the email already exists."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(GENERIC_ERROR)
        return value

    def validate(self, attrs):
        """Check password confirmation match and password strength."""
        if attrs["password"] != attrs["confirmed_password"]:
            raise serializers.ValidationError({"confirmed_password": GENERIC_ERROR})
        self._validate_password_strength(attrs["password"])
        return attrs

    def _validate_password_strength(self, password):
        """Run Django's built-in password validators."""
        try:
            validate_password(password)
        except serializers.ValidationError:
            raise serializers.ValidationError({"password": GENERIC_ERROR})

    def create(self, validated_data):
        validated_data.pop("confirmed_password")
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate the user; Django's ModelBackend already rejects inactive users."""
        request = self.context.get("request")
        user = authenticate(request, email=attrs["email"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError(GENERIC_ERROR)
        attrs["user"] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()