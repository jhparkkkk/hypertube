from rest_framework import serializers
from .models import Comment
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "profile_picture"]
        extra_kwargs = {"email": {"write_only": True}, "profile_picture": {"required": False}}


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    comment = serializers.CharField(source="text")
    date = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "username", "comment", "date", "tmdb_id"]
        read_only_fields = ["id", "username", "date"]
        extra_kwargs = {"tmdb_id": {"write_only": True}}
