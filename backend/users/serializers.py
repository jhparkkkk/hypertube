from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "first_name",
                  "last_name", "password", "auth_provider", "preferred_language", "profile_picture"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "User with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "User with this username already exists.")
        if not re.match(r"^[a-zA-Z0-9_.-]+$", value):
            raise serializers.ValidationError(
                "Username can only contain alphanumeric characters and ._-")
        if len(value) < 3:
            raise serializers.ValidationError(
                "Username must be at least 3 characters long.")
        if len(value) > 30:
            raise serializers.ValidationError(
                "Username must be at most 30 characters long.")
        return value

    def validate_last_name(self, value):
        if not re.match(r"^[A-Za-zÀ-ÿ\-]+$", value):
            raise serializers.ValidationError(
                "Last name must contain only letters and hyphens."
            )
        if len(value) < 2 or len(value) > 30:
            raise serializers.ValidationError(
                "Last name must be between 2 and 30 characters long.")
        return value

    def validate_first_name(self, value):
        if not re.match(r"^[A-Za-zÀ-ÿ\-]+$", value):
            raise serializers.ValidationError(
                "Last name must contain only letters and hyphens."
            )
        if len(value) < 2 or len(value) > 30:
            raise serializers.ValidationError(
                "Last name must be between 2 and 30 characters long.")
        return value

    def validate_password(self, password):
        FORBIDDEN_WORDS = [
            "password", "motdepasse", "admin", "azerty", "qwerty",
            "123456", "abcdef", "welcome", "monkey", "dragon"
        ]

        if len(password) < 8 or len(password) > 50:
            raise ValidationError(
                "Password must be between 8 and 50 characters.")

        if not re.search(r"[A-Za-z]", password):
            raise ValidationError("Password must contain at least one letter.")
        if not re.search(r"\d", password):
            raise ValidationError(
                "Password must contain at least one digit.")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(
                "Password must contain at least one special character.")
        for word in FORBIDDEN_WORDS:
            if word in password.lower():
                raise ValidationError(
                    "Password is too common or insecure.")
        return password

    def validate_preferred_language(self, value):
        allowed_languages = ["en", "fr", "es", "de",
                             "it", "pt", "ru", "ja", "ko", "zh"]
        if value not in allowed_languages:
            raise serializers.ValidationError("Invalid language")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_new_password(self, password):
        FORBIDDEN_WORDS = [
            "password", "motdepasse", "admin", "azerty", "qwerty",
            "123456", "abcdef", "welcome", "monkey", "dragon"
        ]

        if len(password) < 8 or len(password) > 50:
            raise ValidationError(
                "Password must be between 8 and 50 characters.")

        if not re.search(r"[A-Za-z]", password):
            raise ValidationError("Password must contain at least one letter.")
        if not re.search(r"\d", password):
            raise ValidationError(
                "Password must contain at least one digit.")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError(
                "Password must contain at least one special character.")
        for word in FORBIDDEN_WORDS:
            if word in password.lower():
                raise ValidationError(
                    "Password is too common or insecure.")
        return password

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "first_name",
                  "last_name", "preferred_language", "profile_picture"]

    def validate_email(self, value):
        user = self.instance
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError(
                "User with this email already exists.")
        return value

    def validate_username(self, value):
        user = self.instance
        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise serializers.ValidationError(
                "This username is already used by another user.")
        return value
