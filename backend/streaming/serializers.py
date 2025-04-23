from rest_framework import serializers
from .models import MovieFile


class MovieFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieFile
        fields = ["id", "tmdb_id", "file_path", "quality"]
