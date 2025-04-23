from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MovieFile
from .serializers import MovieFileSerializer
from .services import StreamingService
import re
import os
import threading
import libtorrent as lt
import logging
import time
import subprocess

# Regex pattern for parsing range header
range_re = re.compile(r"bytes\s*=\s*(\d+)\s*-\s*(\d*)", re.I)

logger = logging.getLogger(__name__)


def convert_video(input_path, output_path):
    """Convert movie to MP4 format with web-compatible codecs"""
    try:
        # First check if input file exists and is readable
        if not os.path.exists(input_path):
            logging.error(f"Input file does not exist: {input_path}")
            return False

        # Check if we have write permission in output directory
        output_dir = os.path.dirname(output_path)
        if not os.access(output_dir, os.W_OK):
            logging.error(f"No write permission in output directory: {output_dir}")
            return False

        # FFmpeg command with more robust parameters
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-i", input_path,
            "-c:v", "libx264",  # Video codec
            "-preset", "medium",  # Encoding speed preset (medium is a good balance)
            "-crf", "23",  # Quality (lower is better, 18-28 is good)
            "-c:a", "aac",  # Audio codec
            "-b:a", "192k",  # Audio bitrate
            "-movflags", "+faststart",  # Enable fast start for web playback
            "-max_muxing_queue_size", "9999",  # Prevent muxing errors
            "-f", "mp4",  # Force MP4 container format
            output_path
        ]

        # Log the full command for debugging
        logging.info(f"Running FFmpeg command: {' '.join(cmd)}")

        # Run FFmpeg with proper pipe redirection
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Capture output in real-time
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logging.error(f"FFmpeg conversion failed with return code {process.returncode}")
            logging.error(f"FFmpeg stderr: {stderr}")
            # Clean up failed output file if it exists
            if os.path.exists(output_path):
                os.remove(output_path)
            return False

        # Verify the output file exists and has size > 0
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logging.error("Output file is missing or empty")
            return False

        logging.info(f"Successfully converted {input_path} to {output_path}")
        return True

    except Exception as e:
        logging.error(f"Error during video conversion: {str(e)}")
        # Clean up failed output file if it exists
        if os.path.exists(output_path):
            os.remove(output_path)
        return False


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
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
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

        # Download until we have enough data (at least 20%)
        while not handle.status().is_seeding:
            status = handle.status()
            movie_file.download_progress = status.progress * 100
            movie_file.save()
            logging.info(f"Download progress: {status.progress * 100:.2f}%")
            
            # Wait for at least 20% of the file to be downloaded before attempting conversion
            if status.progress >= 0.20:
                break
            time.sleep(1)

        # Ensure the download directory exists
        os.makedirs(os.path.dirname(video_file_path), exist_ok=True)

        # Check if movie needs conversion
        file_ext = os.path.splitext(video_file_path)[1].lower()
        if file_ext in [".mkv", ".avi", ".wmv"]:
            movie_file.download_status = "CONVERTING"
            movie_file.save()
            output_path = video_file_path.rsplit(".", 1)[0] + ".mp4"
            
            # Log the conversion attempt
            logging.info(f"Starting conversion: {video_file_path} -> {output_path}")
            
            if convert_video(video_file_path, output_path):
                logging.info("Conversion successful")
                video_file_path = output_path
            else:
                logging.error("Conversion failed")
                movie_file.download_status = "ERROR"
                movie_file.save()
                return

        movie_file.file_path = video_file_path
        movie_file.download_status = "READY"
        movie_file.save()

    except Exception as e:
        logging.error(f"Error processing movie {video_id}: {str(e)}")
        if "movie_file" in locals():
            movie_file.download_status = "ERROR"
            movie_file.save()


class StreamingViewSet(viewsets.ViewSet):
    """
    ViewSet for streaming operations.
    POST /streaming/:id/start - Start movie download and processing
    GET /streaming/:id/status - Get movie streaming status
    GET /streaming/:id/stream - Stream movie content
    """

    @action(detail=True, methods=["post"], url_path="start")
    def start_stream(self, request, pk=None):
        """Start movie download and processing"""
        magnet_link = request.data.get("magnet_link")
        if not magnet_link:
            return Response({"error": "Magnet link is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Create or get existing movie file
        movie_file, created = MovieFile.objects.get_or_create(tmdb_id=pk, defaults={"magnet_link": magnet_link})

        # If already processing or ready, return current status
        if movie_file.download_status in ["DOWNLOADING", "CONVERTING", "READY"]:
            return Response({"status": movie_file.download_status, "progress": movie_file.download_progress})

        # Start processing in background thread
        thread = threading.Thread(target=process_video_thread, args=(movie_file.id,))
        thread.daemon = True
        thread.start()

        return Response({"status": "PENDING", "message": "Started movie processing"})

    @action(detail=True, methods=["get"], url_path="status")
    def status(self, request, pk=None):
        """Get movie streaming status"""
        try:
            movie_file = MovieFile.objects.get(tmdb_id=pk)
            return Response(
                {
                    "status": movie_file.download_status,
                    "progress": movie_file.download_progress,
                    "file_path": movie_file.file_path if movie_file.download_status == "READY" else None,
                }
            )
        except MovieFile.DoesNotExist:
            return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["get"], url_path="stream")
    def stream(self, request, pk=None):
        """Stream movie content using FFmpeg"""
        try:
            movie_file = MovieFile.objects.get(tmdb_id=pk)
            
            if movie_file.download_status != "READY":
                return Response(
                    {"error": f"Movie is not ready for streaming (status: {movie_file.download_status})"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not os.path.exists(movie_file.file_path):
                return Response(
                    {"error": "Video file not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get start time from query params (for seeking)
            start_time = float(request.query_params.get('start', 0))

            # Initialize streaming service
            streaming_service = StreamingService()
            
            # Stream the video
            response = streaming_service.stream_video(
                file_path=movie_file.file_path,
                start_time=start_time
            )

            return response

        except MovieFile.DoesNotExist:
            return Response(
                {"error": "Movie not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["get"], url_path="file-status")
    def file_status(self, request, pk=None):
        """Get movie file status including download progress"""
        try:
            movie_file = MovieFile.objects.get(tmdb_id=pk)
            return Response({
                "magnet_link": movie_file.magnet_link,
                "download_status": movie_file.download_status,
                "download_progress": movie_file.download_progress,
                "file_path": movie_file.file_path if movie_file.download_status == "READY" else None
            })
        except MovieFile.DoesNotExist:
            return Response({
                "download_status": "NOT_FOUND",
                "download_progress": 0,
                "file_path": None
            })


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
            return Response({"error": "Invalid magnet link format"}, status=status.HTTP_400_BAD_REQUEST)

        movie_file = serializer.save()

        # Start the background thread
        thread = threading.Thread(target=process_video_thread, args=(movie_file.id,))
        thread.daemon = True
        thread.start()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"])
    def start_stream(self, request, pk=None):
        """Start movie download and processing"""
        movie_file = self.get_object()

        # If already processing or ready, return current status
        if movie_file.download_status in ["DOWNLOADING", "CONVERTING", "READY"]:
            return Response({"status": movie_file.download_status, "progress": movie_file.download_progress})

        # Start processing in background thread
        thread = threading.Thread(target=process_video_thread, args=(movie_file.id,))
        thread.daemon = True
        thread.start()

        return Response({"status": "PENDING", "message": "Started movie processing"})

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        """Get current movie processing status"""
        movie_file = self.get_object()
        return Response(
            {"download_status": movie_file.download_status, "download_progress": movie_file.download_progress}
        )

    @action(detail=True, methods=["get"])
    def stream(self, request, pk=None):
        try:
            movie_file = self.get_object()

            if movie_file.download_status != "READY":
                return Response({"error": "Movie not ready"}, status=status.HTTP_400_BAD_REQUEST)

            path = movie_file.file_path
            if not os.path.exists(path):
                return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

            # Get file size and range header
            range_header = request.META.get("HTTP_RANGE", "").strip()

            # Create streaming service
            streaming_service = StreamingService()

            # Stream with FFmpeg
            response = streaming_service.stream_video(
                file_path=path,
                range_header=range_header
            )

            # Add CORS headers
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Range"

            return response

        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            return Response(
                {"error": "Streaming error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
