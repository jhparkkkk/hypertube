import logging
import os
import subprocess
from typing import Optional, Union
from django.http import StreamingHttpResponse, FileResponse
import re
import time

range_re = re.compile(r"bytes\s*=\s*(\d+)\s*-\s*(\d*)", re.I)


class VideoService:
    def __init__(self):
        self.segment_duration = 600  # 10 minutes in seconds
        self.processed_segments = set()
        self.failed_segments = set()
        self.segment_retry_count = {}
        self.segment_last_attempt = {}
        self.max_retries = 3
        self.retry_cooldown = 30  # Wait 30 seconds before retrying a failed segment

    def get_video_duration(self, video_path: str) -> Optional[float]:
        """Get video duration using ffprobe."""
        try:
            cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", video_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except (subprocess.SubprocessError, ValueError, OSError) as e:
            logging.error(f"Error getting video duration: {e}")
            return None

    def convert_segment(self, input_path: str, output_dir: str, current_segment: int, video_duration: float) -> bool:
        """Convert a single segment of the video."""
        start_time = current_segment * self.segment_duration
        file_name = os.path.basename(input_path)
        segment_name = f"{os.path.splitext(file_name)[0]}_segment_{current_segment:03d}.mp4"
        segment_path = os.path.join(output_dir, segment_name)

        # Format time for ffmpeg (HH:MM:SS)
        start_time_str = f"{start_time // 3600:02.0f}:{(start_time % 3600) // 60:02.0f}:{start_time % 60:02.0f}"
        duration_str = f"{min(self.segment_duration, video_duration - start_time)}"

        # Record attempt time
        self.segment_last_attempt[current_segment] = time.time()

        # Use ffmpeg to convert the segment (stream copy for speed)
        ffmpeg_cmd = [
            "ffmpeg",
            "-i",
            input_path,
            "-ss",
            start_time_str,
            "-t",
            duration_str,
            "-c",
            "copy",  # Copy streams without re-encoding
            "-avoid_negative_ts",
            "make_zero",
            "-y",  # Overwrite output file
            segment_path,
        ]

        try:
            retry_info = (
                f" (retry {self.segment_retry_count.get(current_segment, 0) + 1}/{self.max_retries})"
                if self.segment_retry_count.get(current_segment, 0) > 0
                else ""
            )
            logging.info(f"Converting segment {current_segment}{retry_info}...")
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logging.info(
                    f"✓ Converted segment {current_segment}: {segment_name} ({start_time_str} - {duration_str}s)"
                )
                self.processed_segments.add(current_segment)
                return True
            else:
                error_msg = result.stderr.strip()
                logging.error(f"FFmpeg error for segment {current_segment}: {error_msg}")
                self.segment_retry_count[current_segment] = self.segment_retry_count.get(current_segment, 0) + 1
                logging.error(
                    f"✗ Error converting segment {current_segment} (attempt {self.segment_retry_count[current_segment]}/{self.max_retries})"
                )
                return False
        except Exception as e:
            logging.error(f"Exception during segment {current_segment} conversion: {e}")
            self.segment_retry_count[current_segment] = self.segment_retry_count.get(current_segment, 0) + 1
            return False

    def convert_to_mp4(self, input_path: str) -> str:
        """Convert video to MP4 format in segments."""
        output_dir = os.path.dirname(input_path)
        current_segment = 0

        # Get video duration
        video_duration = self.get_video_duration(input_path)
        if not video_duration:
            raise Exception("Could not determine video duration")

        while (current_segment * self.segment_duration) < video_duration:
            # Check cooldown period for retries
            last_attempt_time = self.segment_last_attempt.get(current_segment, 0)
            cooldown_passed = (time.time() - last_attempt_time) >= self.retry_cooldown

            if (
                current_segment not in self.processed_segments
                and self.segment_retry_count.get(current_segment, 0) < self.max_retries
                and (self.segment_retry_count.get(current_segment, 0) == 0 or cooldown_passed)
            ):
                success = self.convert_segment(input_path, output_dir, current_segment, video_duration)

                if success:
                    current_segment += 1
                elif self.segment_retry_count.get(current_segment, 0) >= self.max_retries:
                    self.failed_segments.add(current_segment)
                    logging.error(f"⚠ Skipping segment {current_segment} after {self.max_retries} failed attempts")
                    current_segment += 1

            time.sleep(1)  # Small delay to prevent CPU overload

        if self.failed_segments:
            logging.error(f"Failed segments: {sorted(list(self.failed_segments))}")
            raise Exception(f"Failed to convert segments: {sorted(list(self.failed_segments))}")

        # Return the path to the first segment as the main file
        first_segment = f"{os.path.splitext(input_path)[0]}_segment_000.mp4"
        return first_segment

    def stream_video(self, file_path: str, range_header: str = "", start_time: float = 0) -> Union[StreamingHttpResponse, FileResponse]:
        """Stream video content with support for range requests and segment switching."""
        try:
            # Always try to use segment_000 for initial playback
            base_path = os.path.splitext(file_path)[0]
            if "_segment_" in base_path:
                base_path = base_path.rsplit("_segment_", 1)[0]
            
            # For initial playback or explicit start_time of 0, use first segment
            if start_time == 0:
                segment_path = f"{base_path}_segment_000.mp4"
                if not os.path.exists(segment_path):
                    raise FileNotFoundError(f"Initial segment not found: {segment_path}")
            else:
                # Calculate which segment to use based on start_time
                segment_number = int(start_time / self.segment_duration)
                segment_path = f"{base_path}_segment_{segment_number:03d}.mp4"
                
                # If segment doesn't exist, try to use the last available segment
                if not os.path.exists(segment_path):
                    # Find the last available segment
                    i = segment_number - 1
                    while i >= 0:
                        prev_segment = f"{base_path}_segment_{i:03d}.mp4"
                        if os.path.exists(prev_segment):
                            segment_path = prev_segment
                            break
                        i -= 1
                    if i < 0:
                        # If no previous segment found, try the first segment
                        first_segment = f"{base_path}_segment_000.mp4"
                        if os.path.exists(first_segment):
                            segment_path = first_segment
                        else:
                            raise FileNotFoundError(f"No valid segments found for {file_path}")

            file_size = os.path.getsize(segment_path)
            content_type = 'video/mp4'

            # For initial playback, don't calculate byte_start
            byte_start = 0
            if start_time > 0:
                relative_start_time = start_time % self.segment_duration
                byte_start = int((relative_start_time / self.segment_duration) * file_size)

            if range_header:
                match = range_re.match(range_header)
                if match:
                    first_byte, last_byte = match.groups()
                    first_byte = int(first_byte) if first_byte else byte_start
                    last_byte = int(last_byte) if last_byte else file_size - 1
                    if last_byte >= file_size:
                        last_byte = file_size - 1
                    length = last_byte - first_byte + 1

                    resp = StreamingHttpResponse(
                        self._stream_video_content(segment_path, first_byte, last_byte),
                        status=206,
                        content_type=content_type
                    )
                    resp['Content-Length'] = str(length)
                    resp['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
                    resp['Accept-Ranges'] = 'bytes'
                    resp['Access-Control-Allow-Origin'] = '*'
                    resp['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                    resp['Access-Control-Allow-Headers'] = 'Range'
                    resp['Cache-Control'] = 'no-cache'
                    return resp

            # For initial request without range header, stream from the beginning
            resp = StreamingHttpResponse(
                self._stream_video_content(segment_path, 0, file_size - 1),
                content_type=content_type
            )
            resp['Content-Length'] = str(file_size)
            resp['Accept-Ranges'] = 'bytes'
            resp['Access-Control-Allow-Origin'] = '*'
            resp['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            resp['Access-Control-Allow-Headers'] = 'Range'
            resp['Cache-Control'] = 'no-cache'
            return resp

        except Exception as e:
            logging.error(f"Error streaming video: {str(e)}")
            raise

    def _stream_video_content(self, file_path: str, start: int, end: int):
        """Generator to stream video content in chunks."""
        chunk_size = 8192  # Adjust chunk size if needed
        with open(file_path, 'rb') as f:
            f.seek(start)
            remaining = end - start + 1
            while remaining:
                chunk = min(chunk_size, remaining)
                data = f.read(chunk)
                if not data:
                    break
                remaining -= len(data)
                yield data
