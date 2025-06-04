from django.db import models
from movies.models import MovieFile


class Subtitle(models.Model):
    movie = models.ForeignKey(MovieFile, on_delete=models.CASCADE, related_name='subtitles')
    subtitle_id = models.CharField(max_length=50)
    language = models.CharField(max_length=10)
    download_count = models.IntegerField(default=0)
    hearing_impaired = models.BooleanField(default=False)
    hd = models.BooleanField(default=False)
    fps = models.FloatField(null=True)
    ratings = models.FloatField(default=0)
    from_trusted = models.BooleanField(default=False)
    upload_date = models.DateTimeField()
    release = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('movie', 'subtitle_id', 'language')
        ordering = ['-ratings', '-download_count']

    def __str__(self):
        return f"{self.movie.title} - {self.language} - {self.subtitle_id}"
