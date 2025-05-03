from rest_framework import serializers
from .models import WatchHistory


class WatchHistorySerializer(serializers.ModelSerializer):
    tmdb_id = serializers.IntegerField(source='movie.tmdb_id', read_only=True)

    class Meta:
        model = WatchHistory
        fields = ["id", "user", "movie", "watched_at", "tmdb_id"]
        read_only_fields = ["id", "user", "watched_at", "tmdb_id"]
