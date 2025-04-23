from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import validate_email

import re

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "first_name",
                  "last_name", "password", "auth_provider", "preferred_language"]
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
        if not value.isalpha():
            raise serializers.ValidationError(
                "Last name must contain only letters.")
        if len(value) < 2 or len(value) > 30:
            raise serializers.ValidationError(
                "Last name must be between 2 and 30 characters long.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long.")
        if len(value) > 50:
            raise serializers.ValidationError(
                "Password must be at most 50 characters long")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one digit.")
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one letter.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long.")
        if len(value) > 50:
            raise serializers.ValidationError(
                "Password must be at most 50 characters long")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one digit.")
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one letter.")
        return value

    def validate(self, attributes):
        new_password = self.validate_password(
            self.initial_data.get("new_password"))
        confirm_password = self.validate_password(
            self.initial_data.get("confirm_password"))
        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "username", "first_name",
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
