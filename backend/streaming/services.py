import subprocess
import logging
from django.http import StreamingHttpResponse, HttpResponse
from typing import Optional
import os
import json
from rest_framework import status

logger = logging.getLogger(__name__)


class StreamingService:
	def __init__(self):
		self.chunk_size = 8192  # 8KB chunks
		self.supported_formats = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}

	def _probe_video(self, file_path):
		"""Get video information using ffprobe"""
		try:
			cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path]
			result = subprocess.run(cmd, capture_output=True, text=True)
			if result.returncode == 0:
				return json.loads(result.stdout)
			return None
		except Exception as e:
			logger.error(f"FFprobe error: {str(e)}")
			return None

	def stream_video(self, file_path, start_time=0, quality="720p"):
		"""Stream video using FFmpeg with adaptive quality and seeking support"""
		if not os.path.exists(file_path):
			logger.error(f"File not found: {file_path}")
			return HttpResponse(status=status.HTTP_404_NOT_FOUND)

		# Get video information
		probe_data = self._probe_video(file_path)
		if not probe_data:
			logger.error("Failed to probe video file")
			return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

		# Set video parameters based on quality
		video_params = self._get_video_params(quality)

		try:
			# Base FFmpeg command
			cmd = [
				"ffmpeg",
				"-ss",
				str(start_time),  # Seek position
				"-i",
				file_path,
				"-c:v",
				"libx264",  # Video codec
				"-preset",
				"ultrafast",  # Fastest encoding
				"-tune",
				"zerolatency",  # Minimize latency
				"-c:a",
				"aac",  # Audio codec
				"-ac",
				"2",  # Stereo audio
				"-b:a",
				"128k",  # Audio bitrate
				"-maxrate",
				video_params["maxrate"],
				"-bufsize",
				video_params["bufsize"],
				"-vf",
				f"scale={video_params['scale']}",  # Resolution
				"-movflags",
				"+faststart+frag_keyframe+empty_moov",  # Optimize for streaming
				"-f",
				"mp4",  # Force MP4 format
				"-",  # Output to pipe
			]

			logger.info(f"Starting FFmpeg stream: {' '.join(cmd)}")

			process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)

			def stream_generator():
				try:
					while True:
						chunk = process.stdout.read(self.chunk_size)
						if not chunk:
							break
						yield chunk
				except Exception as e:
					logger.error(f"Streaming error: {str(e)}")
				finally:
					try:
						process.terminate()
						process.wait(timeout=5)
					except subprocess.TimeoutExpired:
						process.kill()

			response = StreamingHttpResponse(stream_generator(), content_type="video/mp4")

			# Add headers for better streaming
			response["Accept-Ranges"] = "bytes"
			response["Cache-Control"] = "no-cache"
			response["X-Accel-Buffering"] = "no"

			return response

		except Exception as e:
			logger.error(f"Failed to start streaming: {str(e)}")
			if "process" in locals():
				try:
					process.terminate()
					process.wait(timeout=5)
				except subprocess.TimeoutExpired:
					process.kill()
			return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

	def _get_video_params(self, quality):
		"""Get video parameters based on quality setting"""
		params = {
			"1080p": {"scale": "-1:1080", "maxrate": "5M", "bufsize": "10M"},
			"720p": {"scale": "-1:720", "maxrate": "2.5M", "bufsize": "5M"},
			"480p": {"scale": "-1:480", "maxrate": "1M", "bufsize": "2M"},
		}
		return params.get(quality, params["720p"])

	def convert_video(self, input_path, output_path):
		"""Convert video to web-compatible format"""
		try:
			cmd = [
				"ffmpeg",
				"-i",
				input_path,
				"-c:v",
				"libx264",
				"-preset",
				"medium",
				"-crf",
				"23",
				"-c:a",
				"aac",
				"-b:a",
				"192k",
				"-movflags",
				"+faststart",
				"-y",
				output_path,
			]

			process = subprocess.run(cmd, capture_output=True, text=True)
			return process.returncode == 0

		except Exception as e:
			logger.error(f"Conversion error: {str(e)}")
			return False

	def get_thumbnail(self, file_path: str, time_position: float = 0) -> Optional[bytes]:
		"""
		Generate a thumbnail from the video at the specified time position
		"""
		try:
			cmd = [
				"ffmpeg",
				"-ss",
				str(time_position),
				"-i",
				file_path,
				"-vframes",
				"1",
				"-f",
				"image2pipe",
				"-vcodec",
				"png",
				"-",
			]
			result = subprocess.run(cmd, capture_output=True)
			return result.stdout if result.returncode == 0 else None
		except Exception as e:
			logger.error("Error generating thumbnail: %s", str(e))
			return None
