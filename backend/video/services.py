import logging
import os
import subprocess
from typing import Optional, Union
from django.http import StreamingHttpResponse, FileResponse
import mimetypes
import re
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

range_re = re.compile(r"bytes\s*=\s*(\d+)\s*-\s*(\d*)", re.I)


class VideoService:
    def __init__(self):
        self.chunk_size = 8192
        self.supported_formats = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
        self.conversion_executor = ThreadPoolExecutor(max_workers=2)
        self.chunk_size_mb = 50  # Size of each chunk in MB

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

    def _get_video_segments(self, input_file: str) -> list[tuple[float, float]]:
        """Get video segments for parallel processing"""
        duration = self._get_duration(input_file)
        if not duration:
            return [(0, 0)]  # Return single segment if duration cannot be determined
        
        segment_duration = 600  # 10 minutes per segment
        segments = []
        current_time = 0
        
        while current_time < duration:
            end_time = min(current_time + segment_duration, duration)
            # Round to nearest second to prevent floating point issues
            segments.append((round(current_time, 0), round(end_time, 0)))
            current_time = end_time
        
        logger.info(f"Split video into {len(segments)} segments: {segments}")
        return segments

    def _convert_segment(self, input_file: str, output_file: str, start_time: float, end_time: float) -> None:
        """Convert a specific segment of the video"""
        # Use rounded values in filename to ensure consistency
        segment_output = f"{output_file}.part_{int(start_time)}_{int(end_time)}.mp4"
        
        # Check if segment already exists and is valid
        if os.path.exists(segment_output) and os.path.getsize(segment_output) > 0:
            logger.info(f"Segment already exists and is valid: {segment_output}")
            return segment_output
            
        logger.info(f"Starting conversion of segment {int(start_time)}-{int(end_time)}")
        
        # Base command for both MP4 and non-MP4 files
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output files
            "-ss", str(int(start_time)),  # Start time (rounded to integer)
            "-i", input_file,  # Input file
            "-t", str(int(end_time - start_time)),  # Duration (rounded to integer)
            "-c:v", "copy" if input_file.lower().endswith('.mp4') else "libx264",  # Copy video codec for MP4, encode for others
            "-c:a", "copy" if input_file.lower().endswith('.mp4') else "aac",  # Copy audio codec for MP4, encode for others
            "-avoid_negative_ts", "1",  # Handle negative timestamps
            "-movflags", "+faststart",  # Enable fast start
            segment_output
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Verify the segment was created successfully
            if os.path.exists(segment_output) and os.path.getsize(segment_output) > 0:
                logger.info(f"Successfully converted segment: {segment_output}")
                return segment_output
            else:
                raise Exception(f"Segment file is empty or missing: {segment_output}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting segment {int(start_time)}-{int(end_time)}: {e.stderr}")
            if os.path.exists(segment_output):
                os.remove(segment_output)
            raise

    def _merge_segments(self, segment_files: list[str], output_file: str) -> None:
        """Merge converted segments into final video"""
        if not segment_files:
            raise ValueError("No segments to merge")
            
        logger.info(f"Starting merge of {len(segment_files)} segments")
        
        # Sort segments by their start time (extracted from filename)
        sorted_segments = sorted(
            segment_files,
            key=lambda x: int(x.split('_')[-2])  # Extract start time from filename as integer
        )
        
        # Create a file list for ffmpeg
        list_file = f"{output_file}.list"
        
        # Check if any segments are missing
        for i in range(len(sorted_segments) - 1):
            current_start = int(sorted_segments[i].split('_')[-2])
            next_start = int(sorted_segments[i + 1].split('_')[-2])
            if next_start - current_start != 600:  # Check for gaps
                raise Exception(f"Gap detected between segments: {current_start} and {next_start}")
        
        with open(list_file, 'w') as f:
            for segment in sorted_segments:
                if not os.path.exists(segment):
                    raise FileNotFoundError(f"Segment file missing: {segment}")
                f.write(f"file '{segment}'\n")
        
        logger.info("Created segment list file for merging")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_file
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Successfully merged segments into: {output_file}")
            
            # Only delete segments and list file after successful merge
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logger.info("Cleaning up temporary files")
                os.remove(list_file)
                for segment in segment_files:
                    if os.path.exists(segment):
                        os.remove(segment)
            else:
                raise Exception("Merged file is empty or does not exist")
                
        except Exception as e:
            logger.error(f"Error during segment merge: {e}")
            if os.path.exists(list_file):
                os.remove(list_file)
            raise

    def convert_to_mp4(self, input_file: str) -> str:
        """Convert or segment video to MP4 format for streaming"""
        output_dir = os.path.join("conversions", os.path.basename(os.path.dirname(input_file)))
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(input_file))[0] + ".mp4")
        
        # Check if output file already exists and is valid
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            logger.info(f"Output file already exists: {output_file}")
            return output_file

        # Get video segments for parallel processing
        segments = self._get_video_segments(input_file)
        logger.info(f"Split video into {len(segments)} segments")
        
        # Convert segments in parallel
        segment_futures = []
        segment_files = []
        
        try:
            # Start all conversions
            for start_time, end_time in segments:
                future = self.conversion_executor.submit(
                    self._convert_segment,
                    input_file,
                    output_file,
                    start_time,
                    end_time
                )
                segment_futures.append(future)

            # Wait for all segments to complete and collect their paths
            for future in segment_futures:
                try:
                    segment_file = future.result()
                    if segment_file and os.path.exists(segment_file):
                        segment_files.append(segment_file)
                    else:
                        raise Exception("Segment conversion failed")
                except Exception as e:
                    logger.error(f"Error processing segment: {e}")
                    raise

            # Only proceed with merge if we have all segments
            if len(segment_files) == len(segments):
                logger.info("All segments converted successfully, proceeding with merge")
                self._merge_segments(segment_files, output_file)
                
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    logger.info(f"Successfully created output file: {output_file}")
                    return output_file
                else:
                    raise Exception("Final output file is empty or does not exist")
            else:
                raise Exception(f"Not all segments were converted successfully. Expected {len(segments)}, got {len(segment_files)}")
                
        except Exception as e:
            logger.error(f"Error during conversion process: {e}")
            # Clean up any completed segments only if we failed
            for segment in segment_files:
                if os.path.exists(segment):
                    logger.info(f"Cleaning up segment: {segment}")
                    os.remove(segment)
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
