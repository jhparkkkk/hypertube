from rest_framework import serializers
from .models import Subtitle


class SubtitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtitle
        fields = [
            'id',
            'subtitle_id',
            'language',
            'download_count',
            'hearing_impaired',
            'hd',
            'fps',
            'ratings',
            'from_trusted',
            'upload_date',
            'release',
            'file_name',
            'url',
        ] 