import logging
import requests
import os
from datetime import datetime
from django.conf import settings
from .models import Subtitle
from movies.models import MovieFile


class SubtitleService:
    BASE_URL = "https://api.opensubtitles.com/api/v1"

    def __init__(self):
        self.headers = {
            "Api-Key": settings.OPENSUBTITLES_API_KEY,
            "Content-Type": "application/json",
            "User-Agent": "Hypertube",
        }

    def fetch_subtitles(self, movie: MovieFile, lang: str) -> list:
        """
        Fetch subtitles for a movie in the specified language from OpenSubtitles API.
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/subtitles",
                headers=self.headers,
                params={
                    "imdb_id": movie.imdb_id,
                    "languages": lang,
                    "order_by": "ratings"
                }
            )
            response.raise_for_status()
            data = response.json()

            subtitles = []
            for item in data.get('data', []):
                attributes = item.get('attributes', {})
                
                # Parse upload date
                upload_date = datetime.strptime(
                    attributes.get('upload_date'),
                    "%Y-%m-%dT%H:%M:%SZ"
                )

                # Get file information
                files = attributes.get('files', [])
                file_id = files[0].get('file_id') if files else None
                file_name = files[0].get('file_name') if files else ''

                subtitle = Subtitle.objects.update_or_create(
                    movie=movie,
                    subtitle_id=attributes.get('subtitle_id'),
                    language=lang,
                    defaults={
                        'download_count': attributes.get('download_count', 0),
                        'hearing_impaired': attributes.get('hearing_impaired', False),
                        'hd': attributes.get('hd', False),
                        'fps': attributes.get('fps'),
                        'ratings': attributes.get('ratings', 0),
                        'from_trusted': attributes.get('from_trusted', False),
                        'upload_date': upload_date,
                        'release': attributes.get('release', ''),
                        'file_name': file_name,
                        'url': attributes.get('url', '')
                    }
                )[0]

                # Download the subtitle if it has a file_id
                if file_id:
                    self.download_subtitle(subtitle, file_id)
                subtitles.append(subtitle)

            return subtitles

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching subtitles: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error while fetching subtitles: {str(e)}")
            return []

    def download_subtitle(self, subtitle: Subtitle, file_id: str) -> bool:
        """
        Download a subtitle file from OpenSubtitles API.
        """
        try:
            # Request download URL
            response = requests.post(
                f"{self.BASE_URL}/download",
                headers=self.headers,
                json={"file_id": file_id}
            )
            response.raise_for_status()
            data = response.json()
            download_url = data.get('link')

            if not download_url:
                logging.error(f"No download URL provided for subtitle {subtitle.subtitle_id}")
                return False

            # Create subtitles directory if it doesn't exist
            subtitles_dir = os.path.join(settings.MEDIA_ROOT, 'subtitles', str(subtitle.movie.id))
            os.makedirs(subtitles_dir, exist_ok=True)

            # Download the subtitle file
            subtitle_path = os.path.join(subtitles_dir, f"{subtitle.language}.srt")
            response = requests.get(download_url)
            response.raise_for_status()

            with open(subtitle_path, 'wb') as f:
                f.write(response.content)

            logging.info(f"Successfully downloaded subtitle to {subtitle_path}")
            return True

        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading subtitle {subtitle.subtitle_id}: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error downloading subtitle {subtitle.subtitle_id}: {str(e)}")
            return False 