import logging
import requests
from typing import Dict, Any, List
from django.conf import settings
import os
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class TMDBService:
    """Service for interacting with The Movie Database API"""

    API_TOKEN = settings.TMDB_API_TOKEN
    BASE_URL = "https://api.themoviedb.org/3"

    @classmethod
    def get_headers(cls):
        """Get the headers for TMDB API requests with Bearer token"""
        if not cls.API_TOKEN:
            logger.error("TMDB_API_TOKEN is not set in environment variables")

        return {"Authorization": f"Bearer {cls.API_TOKEN or ''}", "Content-Type": "application/json;charset=utf-8"}

    @classmethod
    def get_popular_movies(cls, page=1, language="en-US") -> Dict[str, Any]:
        """Get popular movies from TMDB"""
        try:
            url = f"{cls.BASE_URL}/movie/popular"
            params = {"language": language, "page": page}
            response = requests.get(url, params=params, headers=cls.get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching popular movies: {str(e)}")
            return {"results": []}

    @classmethod
    def search_movies(cls, query, page=1, language="en-US") -> Dict[str, Any]:
        """Search for movies by query"""
        try:
            url = f"{cls.BASE_URL}/search/movie"
            params = {"language": language, "query": query, "page": page}
            response = requests.get(url, params=params, headers=cls.get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error searching movies: {str(e)}")
            return {"results": []}

    @classmethod
    def get_movie_details(cls, movie_id, language="en-US") -> Dict[str, Any]:
        """Get detailed information for a specific movie"""
        try:
            url = f"{cls.BASE_URL}/movie/{movie_id}"
            params = {
                "language": language,
                "append_to_response": "credits,videos,images,similar",
            }
            response = requests.get(url, params=params, headers=cls.get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching movie details: {str(e)}")
            return {}


class TorrentService:
    def __init__(self):
        # Get Jackett configuration from environment variables
        self.jackett_url = os.getenv("JACKETT_URL", "http://jackett:9117")
        self.api_key = os.getenv("JACKETT_API_KEY")
        if not self.api_key:
            logger.error("JACKETT_API_KEY not set in environment variables")
        self.min_seeders = 3  # Minimum number of seeders required
        logger.info("TorrentService initialized with URL: %s", self.jackett_url)

    def search_movie_torrents(self, tmdb_id: str = None, title: str = None, year: int = None) -> List[Dict]:
        """
        Search for movie torrents using Jackett API
        Returns a list of available torrents with quality and size information
        """
        try:
            search_term = title
            if year:
                search_term = f"{title} {year}"

            logger.info("Starting search for: %s", search_term)

            search_url = f"{self.jackett_url}/api/v2.0/indexers/all/results"
            params = {
                "apikey": self.api_key,
                "Query": search_term,
                "Category[]": ["2000", "2010", "2020", "2030", "2040", "2045", "2050", "2060"],
                "Type": "search",
            }

            logger.error("DEBUG: Starting Jackett search with URL: %s", search_url)  # Using error level for visibility
            logger.error("DEBUG: Search parameters: %s", params)

            response = requests.get(search_url, params=params, timeout=15)
            logger.error("DEBUG: Jackett response status: %d", response.status_code)
            logger.error("DEBUG: Jackett response headers: %s", dict(response.headers))

            if not response.ok:
                logger.error("Jackett API error: %d - %s", response.status_code, response.text)
                return []

            try:
                data = response.json()
                logger.error("DEBUG: Raw response data keys: %s", list(data.keys()))
                
                results = data.get("Results", [])
                logger.error("DEBUG: Number of results: %d", len(results))
                
                # Log first few results
                for idx, result in enumerate(results[:3]):
                    logger.error("DEBUG: Result %d: %s", idx + 1, {
                        "Title": result.get("Title"),
                        "MagnetUri": result.get("MagnetUri"),
                        "Link": result.get("Link"),
                        "InfoHash": result.get("InfoHash"),
                        "Seeders": result.get("Seeders"),
                        "Size": result.get("Size"),
                        "Tracker": result.get("Tracker")
                    })

            except Exception as e:
                logger.error("Failed to parse Jackett response: %s", str(e))
                logger.error("Raw response text: %s", response.text[:1000])  # First 1000 chars
                return []

            torrent_list = []
            valid_results = 0
            invalid_results = 0

            for result in results:
                try:
                    title = result.get("Title", "Unknown")
                    logger.error("DEBUG: Processing result: %s", title)
                    
                    # Get magnet URI - Jackett usually provides it directly
                    magnet_uri = result.get("MagnetUri")
                    logger.error("DEBUG: Found MagnetUri: %s", bool(magnet_uri))
                    
                    # If no MagnetUri, try the Link field
                    if not magnet_uri:
                        link = result.get("Link")
                        logger.error("DEBUG: No MagnetUri, checking Link: %s", link)
                        if isinstance(link, str) and link.startswith("magnet:?"):
                            magnet_uri = link
                            logger.error("DEBUG: Using Link as magnet")
                    
                    # If still no magnet, try to get info hash
                    if not magnet_uri:
                        info_hash = result.get("InfoHash")
                        logger.error("DEBUG: No magnet link, checking InfoHash: %s", info_hash)
                        if info_hash:
                            magnet_uri = self._create_magnet_link(info_hash, title)
                            logger.error("DEBUG: Created magnet from hash")

                    if not magnet_uri:
                        logger.error("DEBUG: No magnet URI found for: %s", title)
                        invalid_results += 1
                        continue

                    # Parse numeric values safely
                    def safe_int(value, default=0):
                        if not value:
                            return default
                        try:
                            return int(str(value))
                        except (ValueError, TypeError):
                            return default

                    seeders = safe_int(result.get("Seeders"))
                    peers = safe_int(result.get("Peers"))
                    size = safe_int(result.get("Size"))

                    logger.error("DEBUG: Parsed values - Seeders: %d, Peers: %d, Size: %d", seeders, peers, size)

                    # Only include results with seeders
                    if seeders < 1:
                        logger.error("DEBUG: Skipping due to no seeders: %s", title)
                        invalid_results += 1
                        continue

                    torrent = {
                        "title": title,
                        "size": size,
                        "seeders": seeders,
                        "leechers": max(0, peers - seeders),
                        "magnet": magnet_uri,
                        "source": result.get("Tracker", "Unknown"),
                    }

                    logger.error("DEBUG: Adding valid torrent: %s", torrent)
                    valid_results += 1
                    torrent_list.append(torrent)

                except Exception as e:
                    invalid_results += 1
                    logger.error("Error processing result: %s - %s", str(e), result)
                    continue

            # Sort by seeders and size
            torrent_list.sort(key=lambda x: (x["seeders"], x["size"]), reverse=True)
            
            logger.error(
                "DEBUG: Final results - Total: %d, Valid: %d, Invalid: %d",
                len(results), valid_results, invalid_results
            )
            
            return torrent_list

        except requests.Timeout:
            logger.error("Timeout while connecting to Jackett")
            return []
        except requests.ConnectionError as e:
            logger.error("Connection error to Jackett: %s", str(e))
            return []
        except Exception as e:
            logger.error("Error searching for torrents: %s", str(e))
            return []

    @staticmethod
    def _create_magnet_link(info_hash: str, title: str) -> str:
        """Create a magnet link from info hash and title"""
        if not info_hash:
            return ""

        trackers = [
            "udp://tracker.opentrackr.org:1337/announce",
            "udp://open.tracker.cl:1337/announce",
            "udp://9.rarbg.com:2810/announce",
            "udp://tracker.openbittorrent.com:6969/announce",
            "http://tracker.openbittorrent.com:80/announce",
            "udp://opentracker.i2p.rocks:6969/announce",
            "https://opentracker.i2p.rocks:443/announce",
            "udp://www.torrent.eu.org:451/announce",
            "udp://tracker.torrent.eu.org:451/announce",
            "udp://open.stealth.si:80/announce",
        ]

        encoded_title = quote_plus(title)
        tracker_params = "&".join(f"tr={quote_plus(tracker)}" for tracker in trackers)

        return f"magnet:?xt=urn:btih:{info_hash}&dn={encoded_title}&{tracker_params}"
