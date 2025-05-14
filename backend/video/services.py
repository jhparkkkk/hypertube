import logging
import os
import subprocess
from typing import Optional, Union
from django.http import StreamingHttpResponse, FileResponse
import mimetypes
import re

logger = logging.getLogger(__name__)

range_re = re.compile(r"bytes\s*=\s*(\d+)\s*-\s*(\d*)", re.I)


class VideoService:
    def __init__(self):
        self.chunk_size = 8192
        self.supported_formats = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}

    def _get_duration(self, file_path: str) -> Optional[float]:
        """Get video duration using ffprobe"""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error getting duration: {e}")
            return None

    def convert_to_mp4(self, input_file: str) -> str:
        """Convert video to MP4 format"""
        if self.is_mp4(input_file):
            return input_file

        output_dir = os.path.join("conversions", os.path.basename(os.path.dirname(input_file)))
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(input_file))[0] + ".mp4")

        cmd = [
            "ffmpeg",
            "-i",
            input_file,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            "-y",
            output_file,
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_file
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting video: {e.stderr.decode()}")
            raise

    def stream_video(
        self, file_path: str, range_header: str = None, start_time: float = 0
    ) -> Union[FileResponse, StreamingHttpResponse]:
        """Stream video content"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")

        # Get file size
        file_size = os.path.getsize(file_path)

        # Set content type
        content_type = mimetypes.guess_type(file_path)[0] or "video/mp4"

        # If it's an MP4 file, stream it directly with range support
        if self.is_mp4(file_path):
            try:
                # Parse range header
                range_match = range_re.match(range_header or "")
                start_byte = 0
                end_byte = file_size - 1

                if range_match:
                    start_byte = int(range_match.group(1))
                    if range_match.group(2):
                        end_byte = int(range_match.group(2))

                # Calculate content length
                content_length = end_byte - start_byte + 1

                # Create response
                response = FileResponse(
                    open(file_path, "rb"),
                    content_type=content_type,
                    as_attachment=False,
                    status=206 if range_header else 200,
                )

                # Add headers
                response["Accept-Ranges"] = "bytes"
                response["Content-Length"] = str(content_length)
                if range_header:
                    response["Content-Range"] = f"bytes {start_byte}-{end_byte}/{file_size}"

                # Seek to start byte
                response.file_to_stream.seek(start_byte)

                return response

            except Exception as e:
                logger.error(f"Error streaming MP4: {e}")
                raise

        # For non-MP4 files, use FFmpeg for transcoding
        try:
            # Create FFmpeg command for streaming
            cmd = [
                "ffmpeg",
                "-ss",
                str(start_time),  # Start time
                "-i",
                file_path,  # Input file
                "-c:v",
                "libx264",  # Video codec
                "-preset",
                "ultrafast",  # Encoding preset
                "-tune",
                "zerolatency",  # Tuning for streaming
                "-c:a",
                "aac",  # Audio codec
                "-f",
                "mp4",  # Output format
                "-movflags",
                "empty_moov+frag_keyframe+default_base_moof",  # Streaming flags
                "pipe:1",  # Output to pipe
            ]

            # Start FFmpeg process
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8  # 100MB buffer
            )

            # Create response
            response = StreamingHttpResponse(
                streaming_content=(chunk for chunk in iter(lambda: process.stdout.read(self.chunk_size), b"")),
                content_type=content_type,
            )

            # Add headers
            response["Accept-Ranges"] = "bytes"
            response["Content-Length"] = str(file_size)
            response["Cache-Control"] = "no-cache"

            return response

        except Exception as e:
            logger.error(f"Error streaming video: {e}")
            if "process" in locals():
                process.kill()
            raise

    def is_mp4(self, file_path: str) -> bool:
        """Check if the file is an MP4"""
        return file_path.lower().endswith(".mp4")

    def get_mp4_path(self, file_path: str) -> str:
        """Get the path for the MP4 version of the file"""
        output_dir = os.path.join("conversions", os.path.basename(os.path.dirname(file_path)))
        return os.path.join(output_dir, os.path.splitext(os.path.basename(file_path))[0] + ".mp4")
