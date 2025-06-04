import logging
import os
from typing import Optional, Union
from django.http import StreamingHttpResponse, FileResponse
import re
import time
import ffmpeg

range_re = re.compile(r"bytes\s*=\s*(\d+)\s*-\s*(\d*)", re.I)


class VideoService:
    def __init__(self):
        self.segment_duration = 10  # 10 seconds
        self.processed_segments = set()
        self.failed_segments = set()
        self.segment_retry_count = {}
        self.segment_last_attempt = {}
        self.max_retries = 3
        self.retry_cooldown = 30  # Wait 30 seconds before retrying a failed segment

    def get_video_duration(self, video_path: str) -> Optional[float]:
        """Get video duration using ffprobe."""
        try:
            probe = ffmpeg.probe(video_path)
            return float(probe['format']['duration'])
        except ffmpeg.Error as e:
            logging.error(f"Error getting video duration: {e.stderr.decode()}")
            return None
        except Exception as e:
            logging.error(f"Error getting video duration: {e}")
            return None

    def is_web_compatible_mp4(self, input_path: str) -> bool:
        """Check if the MP4 file is already web-compatible."""
        try:
            probe = ffmpeg.probe(input_path)
            format_name = probe['format']['format_name']
            
            # Check if it's an MP4 container
            if 'mp4' not in format_name.lower():
                return False

            # Check video codec
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if not video_stream or video_stream['codec_name'] not in ['h264', 'avc1']:
                return False

            # Check audio codec
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            if not audio_stream or audio_stream['codec_name'] not in ['aac']:
                return False

            return True
        except Exception as e:
            logging.error(f"Error checking MP4 compatibility: {e}")
            return False

    def convert_segment(self, input_path: str, output_dir: str, current_segment: int, video_duration: float) -> bool:
        """Convert a single segment of the video to web-compatible format."""
        start_time = current_segment * self.segment_duration
        
        # Get relative path structure from input_path
        rel_path = os.path.relpath(input_path, output_dir)
        dir_path = os.path.dirname(rel_path)
        file_name = os.path.basename(rel_path)
        base_name = os.path.splitext(file_name)[0]
        segment_name = f"{base_name}_segment_{current_segment:03d}.mp4"
        if dir_path and dir_path != '.':
            segment_path = os.path.join(output_dir, dir_path, segment_name)
            # Ensure the subdirectory exists
            os.makedirs(os.path.dirname(segment_path), exist_ok=True)
        else:
            segment_path = os.path.join(output_dir, segment_name)

        # Record attempt time
        self.segment_last_attempt[current_segment] = time.time()

        try:
            retry_info = (
                f" (retry {self.segment_retry_count.get(current_segment, 0) + 1}/{self.max_retries})"
                if self.segment_retry_count.get(current_segment, 0) > 0
                else ""
            )
            logging.info(f"Converting segment {current_segment}{retry_info}...")

            # Check if input is already a web-compatible MP4
            is_compatible = self.is_web_compatible_mp4(input_path)
            
            if is_compatible:
                # For compatible MP4s, just copy the stream without re-encoding
                stream = (
                    ffmpeg
                    .input(input_path, ss=start_time, t=min(self.segment_duration, video_duration - start_time))
                    .output(
                        segment_path,
                        c='copy',  # Copy streams without re-encoding
                        movflags='frag_keyframe+empty_moov'  # Optimize for web streaming
                    )
                    .overwrite_output()
                )
            else:
                # For other formats, convert to web-compatible format
                stream = (
                    ffmpeg
                    .input(input_path, ss=start_time, t=min(self.segment_duration, video_duration - start_time))
                    .output(
                        segment_path,
                        format='mp4',
                        preset='ultrafast',
                        movflags='frag_keyframe+empty_moov'
                    )
                    .overwrite_output()
                )

            # Run ffmpeg
            stream.run(capture_stdout=True, capture_stderr=True)

            # Verify the output file exists and is valid
            if os.path.exists(segment_path) and os.path.getsize(segment_path) > 0:
                try:
                    ffmpeg.probe(segment_path)
                    logging.info(f"✓ {'Copied' if is_compatible else 'Converted'} segment {current_segment}: {segment_path}")
                    self.processed_segments.add(current_segment)
                    return True
                except ffmpeg.Error as e:
                    logging.error(f"Invalid output file for segment {current_segment}: {e.stderr.decode()}")
                    if os.path.exists(segment_path):
                        os.remove(segment_path)
                    return False
            else:
                logging.error(f"Output file not created for segment {current_segment}")
                return False

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
            logging.error(f"FFmpeg error for segment {current_segment}: {error_msg}")
            self.segment_retry_count[current_segment] = self.segment_retry_count.get(current_segment, 0) + 1
            logging.error(
                f"✗ Error {'copying' if is_compatible else 'converting'} segment {current_segment} "
                f"(attempt {self.segment_retry_count[current_segment]}/{self.max_retries})"
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
        if not os.path.exists(input_path):
            raise Exception("Input file not found")
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
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Video file not found: {file_path}")

            file_size = os.path.getsize(file_path)
            content_type = 'video/mp4'

            # Handle range request
            if range_header:
                try:
                    ranges = range_header.replace('bytes=', '').split('-')
                    first_byte = int(ranges[0])
                    last_byte = int(ranges[1]) if ranges[1] else file_size - 1
                except (IndexError, ValueError):
                    first_byte = 0
                    last_byte = file_size - 1
            else:
                first_byte = 0
                last_byte = file_size - 1

            # Ensure valid range
            if first_byte >= file_size or first_byte < 0:
                first_byte = 0
            if last_byte >= file_size:
                last_byte = file_size - 1

            length = last_byte - first_byte + 1

            # Create response
            response = StreamingHttpResponse(
                self._stream_video_content(file_path, first_byte, last_byte),
                status=206 if range_header else 200,
                content_type=content_type
            )

            # Set headers
            response['Accept-Ranges'] = 'bytes'
            response['Content-Length'] = str(length)
            if range_header:
                response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
            
            # CORS headers
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Range'
            
            # Cache control
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

            return response

        except Exception as e:
            logging.error(f"Error in stream_video: {str(e)}")
            raise

    def _stream_video_content(self, file_path: str, start: int, end: int):
        """Generator to stream video content in chunks."""
        chunk_size = 8192
        try:
            with open(file_path, 'rb') as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = min(chunk_size, remaining)
                    data = f.read(chunk)
                    if not data:
                        break
                    yield data
                    remaining -= len(data)
        except Exception as e:
            logging.error(f"Error in _stream_video_content: {str(e)}")
            raise