import logging
import requests
import os
from django.conf import settings
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
        Fetch and download subtitles for a movie in the specified language from OpenSubtitles API.
        Returns a list of downloaded subtitle information.
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/subtitles",
                headers=self.headers,
                params={
                    "tmdb_id": movie.tmdb_id,
                    "languages": lang,
                    "order_by": "ratings"
                }
            )
            response.raise_for_status()
            data = response.json()
            print(data)

            subtitles = []
            for item in data.get('data', []):
                attributes = item.get('attributes', {})
                files = attributes.get('files', [])
                if files:
                    file_id = files[0].get('file_id')
                    if file_id:
                        try:
                            download_response = requests.post(
                                f"{self.BASE_URL}/download",
                                headers=self.headers,
                                json={"file_id": file_id}
                            )
                            download_response.raise_for_status()
                            download_data = download_response.json()
                            download_url = download_data.get('link')

                            if download_url:
                                subtitles_dir = os.path.join(settings.MEDIA_ROOT, 'downloads/subtitles', str(movie.tmdb_id))
                                os.makedirs(subtitles_dir, exist_ok=True)

                                subtitle_path = os.path.join(subtitles_dir, f"{lang}.srt")
                                file_response = requests.get(download_url)
                                file_response.raise_for_status()

                                with open(subtitle_path, 'wb') as f:
                                    f.write(file_response.content)

                                subtitles.append({
                                    'language': attributes.get('language', lang),
                                    'language_name': 'English' if lang == 'en' else lang.upper(),
                                    'from_trusted': attributes.get('from_trusted', False),
                                    'download_count': attributes.get('download_count', 0),
                                    'ratings': attributes.get('ratings', 0),
                                    'hearing_impaired': attributes.get('hearing_impaired', False),
                                    'hd': attributes.get('hd', False),
                                    'fps': attributes.get('fps', 0),
                                    'release': attributes.get('release', ''),
                                    'upload_date': attributes.get('upload_date', ''),
                                    'file_path': os.path.join('subtitles', str(movie.tmdb_id), f"{lang}.srt")
                                })
                                logging.info(f"Successfully downloaded subtitle to {subtitle_path}")
                                break

                        except requests.exceptions.RequestException as e:
                            logging.error(f"Error downloading subtitle with file_id {file_id}: {str(e)}")
                            continue
                        except Exception as e:
                            logging.error(f"Unexpected error downloading subtitle with file_id {file_id}: {str(e)}")
                            continue

            return subtitles

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching subtitles: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error while fetching subtitles: {str(e)}")
            return [] 