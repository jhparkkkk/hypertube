import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class VideoService:
    def __init__(self):
        self.chunk_size = 8192
        self.supported_formats = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
        self.chunk_duration = 10

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

    def _convert_chunk(self, input_file: str, start_time: float, duration: float, output_file: str) -> bool:
        """Convert a chunk of video"""
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_file,
            "-ss",
            str(start_time),
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-vf",
            "format=yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            "-f",
            "mp4",
            output_file,
        ]
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting chunk: {e}")
            return False

    def get_chunk_path(self, file_path: str, chunk_index: int) -> str:
        """Get the path for a specific chunk"""
        output_dir = f"conversions/{os.path.basename(file_path)}"
        return f"{output_dir}/chunk_{chunk_index}.mp4"

    def ensure_chunk_directory(self, file_path: str) -> str:
        """Ensure the chunk directory exists and return its path"""
        output_dir = f"conversions/{os.path.basename(file_path)}"
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def is_mp4(self, file_path: str) -> bool:
        """Check if the file is an MP4"""
        return file_path.lower().endswith(".mp4")

    def get_mp4_path(self, file_path: str) -> str:
        """Get the path for the MP4 version of the file"""
        output_dir = f"conversions/{os.path.basename(file_path)}"
        return f"{output_dir}/full.mp4"

    def process_next_chunk(self, input_file: str, last_processed_time: float) -> tuple[bool, float]:
        """
        Process the next chunk of video
        Returns: (success, new_last_processed_time)
        """
        if self.is_mp4(input_file):
            return False, last_processed_time

        current_duration = self._get_duration(input_file)
        if current_duration is None:
            return False, last_processed_time

        if last_processed_time >= current_duration:
            return False, last_processed_time

        next_chunk_end = min(last_processed_time + self.chunk_duration, current_duration)
        chunk_index = int(last_processed_time / self.chunk_duration)

        self.ensure_chunk_directory(input_file)
        output_file = self.get_chunk_path(input_file, chunk_index)

        logger.info(f"Converting chunk {chunk_index} from {last_processed_time} to {next_chunk_end}")

        if self._convert_chunk(input_file, last_processed_time, self.chunk_duration, output_file):
            return True, next_chunk_end
        else:
            return False, last_processed_time

    def get_available_chunks(self, file_path: str) -> list[str]:
        """Get list of available converted chunks or the full MP4 file"""
        if self.is_mp4(file_path):
            mp4_path = self.get_mp4_path(file_path)
            return [mp4_path] if os.path.exists(mp4_path) else []

        output_dir = f"conversions/{os.path.basename(file_path)}"
        if not os.path.exists(output_dir):
            return []

        chunks = []
        i = 0
        while True:
            chunk_path = self.get_chunk_path(file_path, i)
            if not os.path.exists(chunk_path):
                break
            chunks.append(chunk_path)
            i += 1
        return chunks

    def is_conversion_complete(self, file_path: str) -> bool:
        """Check if the entire file has been converted"""
        if self.is_mp4(file_path):
            return os.path.exists(self.get_mp4_path(file_path))

        total_duration = self._get_duration(file_path)
        if total_duration is None:
            return False

        chunks = self.get_available_chunks(file_path)
        expected_chunks = int((total_duration + self.chunk_duration - 1) / self.chunk_duration)
        return len(chunks) >= expected_chunks
