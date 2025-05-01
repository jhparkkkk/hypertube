from django.db import models
from django.conf import settings
from movies.models import MovieFile


class WatchHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watch_history")
    movie = models.ForeignKey(
        MovieFile, on_delete=models.CASCADE, related_name="watched_by")
    watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "movie")
        ordering = ["-watched_at"]

    def __str__(self):
        return f"{self.user.username} watched {self.movie.tmdb_id}"
