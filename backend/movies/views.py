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
from django.utils import timezone
from datetime import timedelta

# Regex pattern for parsing range header
range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)


def convert_video(input_path, output_path):
    """Convert movie to MKV format with web-compatible codecs"""
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", "libx264",  # Video codec
        "-preset", "fast",  # Encoding speed preset
        "-crf", "23",      # Quality (lower is better, 18-28 is good)
        "-c:a", "aac",     # Audio codec
        "-b:a", "128k",    # Audio bitrate
        "-f", "matroska",  # Force MKV container format
        "-y",              # Overwrite output file
        output_path
    ]
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        success = process.returncode == 0
        if not success:
            logging.error(f"FFmpeg conversion failed: {stderr.decode()}")
        return success
    except Exception as e:
        logging.error(f"Error during video conversion: {str(e)}")
        return False


def download_subtitles(imdb_id, save_path):
    """Download English subtitles using OpenSubtitles API"""
    # Implement subtitle download logic here
    pass


class TorrentSessionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TorrentSessionManager, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    def _initialize(self):
        self.session = lt.session()
        self.session.listen_on(6881, 6891)
        self.handles = {}
        self.handle_locks = {}
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def _cleanup_loop(self):
        while True:
            try:
                with self._lock:
                    for handle_id, handle in list(self.handles.items()):
                        if handle.is_valid() and handle.status().is_seeding:
                            # Keep seeding for a while to help others
                            if handle.status().active_time > 3600:  # 1 hour
                                self.remove_torrent(handle_id)
            except Exception as e:
                logging.error(f"Error in cleanup loop: {str(e)}")
            time.sleep(300)  # Check every 5 minutes

    def add_torrent(self, magnet_link, save_path):
        params = lt.parse_magnet_uri(magnet_link)
        params.save_path = save_path

        with self._lock:
            handle = self.session.add_torrent(params)
            handle_id = str(hash(magnet_link))
            self.handles[handle_id] = handle
            self.handle_locks[handle_id] = threading.Lock()
            return handle_id

    def get_handle(self, handle_id):
        return self.handles.get(handle_id)

    def get_handle_lock(self, handle_id):
        return self.handle_locks.get(handle_id)

    def remove_torrent(self, handle_id):
        with self._lock:
            if handle_id in self.handles:
                handle = self.handles[handle_id]
                if handle.is_valid():
                    self.session.remove_torrent(handle)
                del self.handles[handle_id]
                del self.handle_locks[handle_id]


# Global session manager
torrent_manager = TorrentSessionManager()


def process_video_thread(video_id):
    try:
        movie_file = MovieFile.objects.get(id=video_id)
        movie_file.download_status = "DOWNLOADING"
        movie_file.save()

        # Ensure download directory exists
        os.makedirs(settings.DOWNLOAD_PATH, exist_ok=True)
        logging.info(f"Using download path: {settings.DOWNLOAD_PATH}")

        # Add torrent to session manager
        handle_id = torrent_manager.add_torrent(
            movie_file.magnet_link, str(settings.DOWNLOAD_PATH))
        handle = torrent_manager.get_handle(handle_id)
        handle_lock = torrent_manager.get_handle_lock(handle_id)

        if not handle:
            logging.error(f"Failed to get torrent handle for movie {video_id}")
            movie_file.download_status = "ERROR"
            movie_file.save()
            return

        with handle_lock:
            while not handle.has_metadata():
                time.sleep(1)

            torrent_info = handle.get_torrent_info()
            largest_file = max(torrent_info.files(), key=lambda f: f.size)
            downloaded_path = os.path.join(
                str(settings.DOWNLOAD_PATH), largest_file.path)

            # Create subdirectories if needed
            os.makedirs(os.path.dirname(downloaded_path), exist_ok=True)

            # Set the file path immediately so streaming can start
            movie_file.file_path = downloaded_path
            movie_file.save()

            # Set sequential download and piece priorities
            handle.set_sequential_download(True)
            num_pieces = torrent_info.num_pieces()
            piece_priorities = [7] * num_pieces  # High priority for all pieces
            handle.prioritize_pieces(piece_priorities)

            # Monitor download progress
            while True:
                status = handle.status()
                progress = status.progress * 100
                movie_file.download_progress = progress
                movie_file.save()

                logging.info(f"Download progress: {progress:.2f}%")

                if status.is_seeding:
                    break

                time.sleep(1)

            # Once download is complete, convert to web-compatible format if needed
            final_path = os.path.join(
                str(settings.DOWNLOAD_PATH),
                f"{movie_file.tmdb_id}_{int(time.time())}.mkv"
            )

            logging.info(
                f"Converting video: {downloaded_path} -> {final_path}")
            if convert_video(downloaded_path, final_path):
                movie_file.file_path = final_path
                movie_file.download_status = "READY"
                # Remove the original file
                if os.path.exists(downloaded_path):
                    try:
                        os.remove(downloaded_path)
                    except Exception as e:
                        logging.error(
                            f"Error removing original file: {str(e)}")
            else:
                movie_file.download_status = "ERROR"
                if os.path.exists(final_path):
                    try:
                        os.remove(final_path)
                    except Exception as e:
                        logging.error(
                            f"Error removing failed conversion: {str(e)}")

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
    GET /movies/:id/stream - Stream movie
    GET /movies/:id/status - Get movie status
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
        """List popular movies or search by query"""
        try:
            search_query = request.query_params.get('search', '').strip()
            page = request.query_params.get('page', 1)

            if search_query:
                # Search for movies
                response = requests.get(
                    "https://api.themoviedb.org/3/search/movie",
                    params={
                        "api_key": settings.TMDB_API_KEY,
                        "query": search_query,
                        "page": page,
                        "include_adult": False
                    }
                )
            else:
                # Get popular movies
                response = requests.get(
                    "https://api.themoviedb.org/3/movie/popular",
                    params={
                        "api_key": settings.TMDB_API_KEY,
                        "page": page
                    }
                )

            response.raise_for_status()
            data = response.json()

            # Filter out movies without posters
            movies = [movie for movie in data["results"]
                      if movie.get("poster_path")]

            return Response({
                "results": [{
                            "id": movie["id"],
                            "title": movie["title"],
                            "poster_path": movie["poster_path"],
                            "vote_average": movie["vote_average"],
                            "release_date": movie.get("release_date", ""),
                            "overview": movie.get("overview", "")
                            } for movie in movies],
                "page": data["page"],
                "total_pages": data["total_pages"]
            })
        except requests.RequestException:
            return Response(
                {"error": "Failed to fetch movies"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, pk=None):
        """Get detailed movie information and magnet link"""
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

        # Try to get existing movie file first
        try:
            movie_file = MovieFile.objects.get(tmdb_id=pk)
            movie["magnet_link"] = movie_file.magnet_link
            movie["download_status"] = movie_file.download_status
            movie["download_progress"] = movie_file.download_progress
        except MovieFile.DoesNotExist:
            # Search for best available torrent
            torrents = TorrentService.search_movie_torrents(
                imdb_id=imdb_id,
                title=movie["title"],
                year=int(movie["release_date"][:4]) if movie.get(
                    "release_date") else None
            )

            if torrents:
                # Select best quality torrent with most seeders
                best_torrent = max(torrents, key=lambda t: (
                    2 if t["quality"] == "1080p" else
                    3 if t["quality"] == "2160p" else
                    1 if t["quality"] == "720p" else 0,
                    t["seeders"]
                ))
                movie["magnet_link"] = best_torrent["magnet_link"]
            else:
                movie["magnet_link"] = None

        return Response(movie)

    @action(detail=True, methods=["post"])
    def start_stream(self, request, pk=None):
        """Start movie download and processing"""
        magnet_link = request.data.get("magnet_link")

        if not magnet_link:
            return Response(
                {"error": "Magnet link is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or get existing movie file
        movie_file, created = MovieFile.objects.get_or_create(
            tmdb_id=pk,
            defaults={"magnet_link": magnet_link}
        )
        # if created:
        #     return Response({
        #         "status": "CREATED",
        #         "message": "MovieFile created without starting download"
        #     }, status=status.HTTP_201_CREATED)

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

    @action(detail=True, methods=["get"], url_path="stream")
    def stream(self, request, pk=None):
        """Stream the movie file progressively"""
        try:
            # Try to find movie by MovieFile ID first, then by TMDB ID
            try:
                movie_file = MovieFile.objects.get(id=pk)
            except MovieFile.DoesNotExist:
                movie_file = MovieFile.objects.get(tmdb_id=pk)

            # Allow streaming if file is ready or has enough buffer for streaming
            if movie_file.download_status not in ["READY", "DOWNLOADING"]:
                return Response(
                    {"error": "Movie not available for streaming"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not movie_file.file_path:
                return Response(
                    {"error": "Movie file path not set"},
                    status=status.HTTP_404_NOT_FOUND
                )

            file_path = movie_file.file_path
            if not os.path.exists(file_path):
                logging.error(f"File not found at path: {file_path}")
                return Response(
                    {"error": "Movie file not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get the file size
            file_size = os.path.getsize(file_path)
            logging.info(f"Streaming file: {file_path}, size: {file_size}")

            # Initialize downloaded_size
            downloaded_size = file_size  # Default to full size for READY status
            current_piece = None
            handle = None

            # If downloading, check if we have enough buffer
            if movie_file.download_status == "DOWNLOADING":
                # Get handle from torrent manager
                for h in torrent_manager.session.get_torrents():
                    if h.status().save_path == os.path.dirname(file_path):
                        handle = h
                        break

                if handle:
                    torrent_info = handle.get_torrent_info()
                    piece_length = torrent_info.piece_length()
                    num_pieces = torrent_info.num_pieces()
                    downloaded_size = sum(1 for i in range(
                        num_pieces) if handle.have_piece(i)) * piece_length
                    current_piece = downloaded_size // piece_length

                    # If less than 5% is downloaded, don't allow streaming yet
                    if downloaded_size < file_size * 0.05:
                        return Response(
                            {"error": "Not enough buffer for streaming"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Set sequential download for better streaming
                    handle.set_sequential_download(True)

                    # Prioritize next pieces
                    if current_piece is not None:
                        for i in range(current_piece, min(current_piece + 100, num_pieces)):
                            handle.piece_priority(i, 7)  # High priority

            # Handle range request
            range_header = request.META.get('HTTP_RANGE', '').strip()
            range_match = range_re.match(range_header)

            if range_match:
                first_byte, last_byte = range_match.groups()
                first_byte = int(first_byte) if first_byte else 0
                last_byte = int(last_byte) if last_byte else file_size - 1

                # Don't allow seeking beyond downloaded portion if still downloading
                if movie_file.download_status == "DOWNLOADING" and first_byte > downloaded_size:
                    return Response(
                        {"error": "Requested range not yet available"},
                        status=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE
                    )

                if last_byte >= file_size:
                    last_byte = file_size - 1

                length = last_byte - first_byte + 1

                response = StreamingHttpResponse(
                    self.range_iter(file_path, first_byte, chunk_size=8192),
                    status=206,
                    content_type='video/mp4'
                )
                response['Content-Length'] = str(length)
                response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
            else:
                response = StreamingHttpResponse(
                    FileWrapper(open(file_path, 'rb')),
                    content_type='video/mp4'
                )
                response['Content-Length'] = str(file_size)

            # Set response headers for streaming
            response['Accept-Ranges'] = 'bytes'
            response['Cache-Control'] = 'no-cache'
            response['X-Content-Type-Options'] = 'nosniff'
            response['Content-Disposition'] = 'inline'

            # Update last watched timestamp
            movie_file.last_watched = timezone.now()
            movie_file.save()

            return response

        except MovieFile.DoesNotExist:
            return Response(
                {"error": "Movie not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logging.error(f"Error streaming movie {pk}: {str(e)}")
            return Response(
                {"error": "Error streaming movie"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def range_iter(self, file_path, start=0, chunk_size=8192):
        """Iterator to stream file in chunks"""
        try:
            with open(file_path, 'rb') as f:
                f.seek(start)
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    yield data
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {str(e)}")
            raise

    @action(detail=True, methods=["get"], url_path="status")
    def status(self, request, pk=None):
        """Get current movie processing status"""
        try:
            movie_file = MovieFile.objects.get(tmdb_id=pk)
            status_response = {
                "status": movie_file.download_status,
                "progress": movie_file.download_progress,
                "movie_file_id": str(movie_file.id)
            }

            # If downloading, check if we have enough buffer for streaming
            if movie_file.download_status == "DOWNLOADING":
                # Consider streamable if more than 5% downloaded
                if movie_file.download_progress >= 5:
                    status_response["streamable"] = True
                else:
                    status_response["streamable"] = False
                    status_response["buffer_needed"] = 5 - \
                        movie_file.download_progress

            return Response(
                status_response,
                content_type='application/json'
            )
        except MovieFile.DoesNotExist:
            return Response(
                {
                    "status": "NOT_FOUND",
                    "progress": 0,
                    "streamable": False
                },
                content_type='application/json'
            )


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
                content_type="video/x-matroska",
            )
            response["Content-Length"] = str(length)
            response["Content-Range"] = f"bytes {first_byte}-{last_byte}/{file_size}"
        else:
            response = StreamingHttpResponse(
                FileWrapper(open(path, "rb")),
                content_type="video/x-matroska"
            )
            response["Content-Length"] = str(file_size)

        response["Accept-Ranges"] = "bytes"
        return response

    def range_iter(self, file_path, start, chunk_size):
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = chunk_size
            while remaining > 0:
                chunk = min(remaining, chunk_size)
                data = f.read(chunk)
                if not data:
                    break
                remaining -= len(data)
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
