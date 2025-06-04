from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
import os


class MovieFile(models.Model):
	"""Model for movie file and streaming information"""
	tmdb_id = models.IntegerField()  # TMDB movie ID
	imdb_id = models.CharField(max_length=20, null=True, blank=True)  # IMDB ID without 'tt' prefix
	magnet_link = models.TextField()
	file_path = models.CharField(max_length=1000, null=True, blank=True)
	download_status = models.CharField(
		max_length=20,
		choices=[
			("PENDING", "Pending"),
			("DOWNLOADING", "Downloading"),
			("READY", "Ready"),
			("ERROR", "Error"),
			("CONVERTING", "Converting"),
		],
		default="PENDING",
	)
	download_progress = models.FloatField(default=0)
	last_watched = models.DateTimeField(null=True, blank=True)
	subtitles_path = models.CharField(max_length=1000, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def save(self, *args, **kwargs):
		# Check if file should be deleted (unwatched for a month)
		if self.last_watched:
			month_ago = timezone.now() - timedelta(days=30)
			if self.last_watched < month_ago:
				if self.file_path and os.path.exists(self.file_path):
					os.remove(self.file_path)
				if self.subtitles_path and os.path.exists(self.subtitles_path):
					os.remove(self.subtitles_path)
				self.file_path = None
				self.subtitles_path = None
				self.download_status = "PENDING"
				self.download_progress = 0

		super().save(*args, **kwargs)


class Comment(models.Model):
	"""Model for movie comments"""
	tmdb_id = models.IntegerField()  # TMDB movie ID
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]
