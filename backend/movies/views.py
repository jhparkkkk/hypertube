from django.http import StreamingHttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MovieFile, Comment
from .serializers import MovieFileSerializer, CommentSerializer
from wsgiref.util import FileWrapper
import re
import os
import threading
import libtorrent as lt
import logging
import time
import subprocess
from django.conf import settings
import requests
from rest_framework.pagination import PageNumberPagination
from rest_framework import permissions
from .services import TorrentService

range_re = re.compile(r"bytes\s*=\s*(\d+)\s*-\s*(\d*)", re.I)


def convert_video(input_path, output_path):
	"""Convert movie to MP4 format"""
	cmd = ["ffmpeg", "-i", input_path, "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", output_path]
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	return process.returncode == 0


def download_subtitles(imdb_id, save_path):
	"""Download English subtitles using OpenSubtitles API"""
	# Implement subtitle download logic here
	pass


def process_video_thread(video_id):
	try:
		movie_file = MovieFile.objects.get(id=video_id)
		movie_file.download_status = "DOWNLOADING"
		movie_file.save()

		# Configure libtorrent parameters
		params = lt.parse_magnet_uri(movie_file.magnet_link)
		params.save_path = "/app/downloads"

		session = lt.session()
		handle = session.add_torrent(params)

		while not handle.has_metadata():
			time.sleep(1)

		torrent_info = handle.get_torrent_info()
		largest_file = max(torrent_info.files(), key=lambda f: f.size)
		video_file_path = os.path.join("/app/downloads", largest_file.path)

		# Download until we have enough data
		while not handle.status().is_seeding:
			status = handle.status()
			movie_file.download_progress = status.progress * 100
			movie_file.save()
			if status.progress >= 0.05:
				break

		# Check if movie needs conversion
		file_ext = os.path.splitext(video_file_path)[1].lower()
		if file_ext in [".mkv", ".avi", ".wmv"]:
			movie_file.download_status = "CONVERTING"
			movie_file.save()
			output_path = video_file_path.rsplit(".", 1)[0] + ".mp4"
			if convert_video(video_file_path, output_path):
				video_file_path = output_path

		# Download subtitles if available
		if movie_file.imdb_id:
			subtitle_path = download_subtitles(movie_file.imdb_id, "/app/downloads/subtitles")
			if subtitle_path:
				movie_file.subtitles_path = subtitle_path

		movie_file.file_path = video_file_path
		movie_file.download_status = "READY"
		movie_file.save()

	except Exception as e:
		logging.error(f"Error processing movie {video_id}: {str(e)}")
		if "movie_file" in locals():
			movie_file.download_status = "ERROR"
			movie_file.save()


class MovieViewSet(viewsets.ViewSet):
	"""
	ViewSet for movie operations using TMDB API.
	GET /movies - List popular movies or search by query
	GET /movies/:id - Detailed movie info
	"""
	pagination_class = PageNumberPagination

	def get_tmdb_movie_details(self, movie_id):
		"""Fetch movie details from TMDB API"""
		try:
			response = requests.get(
				f"https://api.themoviedb.org/3/movie/{movie_id}",
				params={"api_key": settings.TMDB_API_KEY}
			)
			response.raise_for_status()
			movie = response.json()

			# Get comment count for the movie using tmdb_id
			comment_count = Comment.objects.filter(tmdb_id=movie_id).count()
			movie["comment_count"] = comment_count

			return movie
		except requests.RequestException:
			return None

	def list(self, request):
		"""List popular movies from TMDB"""
		try:
			response = requests.get(
				"https://api.themoviedb.org/3/movie/popular",
				params={"api_key": settings.TMDB_API_KEY}
			)
			response.raise_for_status()
			movies = response.json()["results"]
			return Response([{
				"id": movie["id"],
				"title": movie["title"],
				"poster_path": movie["poster_path"],
				"vote_average": movie["vote_average"],
				"release_date": movie["release_date"]
			} for movie in movies])
		except requests.RequestException:
			return Response(
				{"error": "Failed to fetch movies"},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)

	def retrieve(self, request, pk=None):
		"""Get detailed movie information and available torrents"""
		movie = self.get_tmdb_movie_details(pk)
		if not movie:
			return Response(
				{"error": "Movie not found"},
				status=status.HTTP_404_NOT_FOUND
			)

		# Get IMDB ID from TMDB for better torrent search
		try:
			external_ids = requests.get(
				f"https://api.themoviedb.org/3/movie/{pk}/external_ids",
				params={"api_key": settings.TMDB_API_KEY}
			).json()
			imdb_id = external_ids.get("imdb_id")
		except requests.RequestException:
			imdb_id = None

		# Search for available torrents
		torrents = TorrentService.search_movie_torrents(
			imdb_id=imdb_id,
			title=movie["title"],
			year=int(movie["release_date"][:4]) if movie.get("release_date") else None
		)

		# Add torrents to movie details
		movie["torrents"] = torrents
		return Response(movie)


class MovieFileViewSet(viewsets.ModelViewSet):
	"""
	ViewSet for handling movie files and streaming.
	Handles torrent downloads and video streaming.
	"""
	queryset = MovieFile.objects.all()
	serializer_class = MovieFileSerializer

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		# Validate magnet link format
		magnet_link = serializer.validated_data["magnet_link"]
		if not magnet_link.startswith("magnet:?"):
			return Response(
				{"error": "Invalid magnet link format"}, 
				status=status.HTTP_400_BAD_REQUEST
			)

		movie_file = serializer.save()

		# Start the background thread
		thread = threading.Thread(
			target=process_video_thread, 
			args=(movie_file.id,)
		)
		thread.daemon = True
		thread.start()

		headers = self.get_success_headers(serializer.data)
		return Response(
			serializer.data, 
			status=status.HTTP_201_CREATED, 
			headers=headers
		)

	@action(detail=True, methods=["post"])
	def start_stream(self, request, pk=None):
		"""Start movie download and processing"""
		movie_file = self.get_object()
		
		# If already processing or ready, return current status
		if movie_file.download_status in ["DOWNLOADING", "CONVERTING", "READY"]:
			return Response({
				"status": movie_file.download_status,
				"progress": movie_file.download_progress
			})

		# Start processing in background thread
		thread = threading.Thread(
			target=process_video_thread,
			args=(movie_file.id,)
		)
		thread.daemon = True
		thread.start()

		return Response({
			"status": "PENDING",
			"message": "Started movie processing"
		})

	@action(detail=True, methods=["get"])
	def status(self, request, pk=None):
		"""Get current movie processing status"""
		movie_file = self.get_object()
		return Response({
			"download_status": movie_file.download_status,
			"download_progress": movie_file.download_progress
		})

	@action(detail=True, methods=["get"])
	def stream(self, request, pk=None):
		movie_file = self.get_object()

		if movie_file.download_status != "READY":
			return Response(
				{"error": "Movie not ready"}, 
				status=status.HTTP_400_BAD_REQUEST
			)

		path = movie_file.file_path
		file_size = os.path.getsize(path)

		range_header = request.META.get("HTTP_RANGE", "").strip()
		range_match = range_re.match(range_header)

		if range_match:
			first_byte, last_byte = range_match.groups()
			first_byte = int(first_byte) if first_byte else 0
			last_byte = int(last_byte) if last_byte else file_size - 1
			length = last_byte - first_byte + 1

			response = StreamingHttpResponse(
				self.range_iter(path, first_byte),
				status=206,
				content_type="video/mp4",
			)
			response["Content-Length"] = str(length)
			response["Content-Range"] = f"bytes {first_byte}-{last_byte}/{file_size}"
		else:
			response = StreamingHttpResponse(
				FileWrapper(open(path, "rb")), 
				content_type="video/mp4"
			)
			response["Content-Length"] = str(file_size)

		response["Accept-Ranges"] = "bytes"
		return response

	def range_iter(self, file_path, start, chunk_size=8192):
		with open(file_path, "rb") as f:
			f.seek(start)
			while True:
				data = f.read(chunk_size)
				if not data:
					break
				yield data


class CommentViewSet(viewsets.ModelViewSet):
	"""
	ViewSet for handling comments.
	GET /comments - List of latest comments
	GET /comments/:id - Single comment details
	POST /comments - Create new comment
	PATCH /comments/:id - Update comment
	DELETE /comments/:id - Delete comment
	"""
	serializer_class = CommentSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return Comment.objects.all().order_by('-created_at')

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)

	def update(self, request, *args, **kwargs):
		"""PATCH /comments/:id - Only allow updating comment text"""
		instance = self.get_object()
		
		# Only allow updating if user is the comment author
		if instance.user != request.user:
			return Response(
				{"error": "Not authorized to update this comment"},
				status=status.HTTP_403_FORBIDDEN
			)
		
		# Only allow updating the comment text
		serializer = self.get_serializer(
			instance, 
			data={"text": request.data.get("comment")},
			partial=True
		)
		serializer.is_valid(raise_exception=True)
		self.perform_update(serializer)
		return Response(serializer.data)
