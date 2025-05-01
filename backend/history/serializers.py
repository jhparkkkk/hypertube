from rest_framework import serializers
from .models import WatchHistory


class WatchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchHistory
        fields = ["id", "user", "movie", "watched_at"]
        read_only_fields = ["id", "user", "watched_at"]
