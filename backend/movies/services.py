import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class TorrentService:
    YTS_API_BASE = "https://yts.mx/api/v2"

    @staticmethod
    def search_movie_torrents(imdb_id: str = None, tmdb_id: str = None, title: str = None, year: int = None) -> List[Dict]:
        """
        Search for movie torrents using YTS API
        Returns a list of available torrents with quality and size information
        """
        try:
            # First try to search by IMDB id if available
            if imdb_id:
                params = {"imdb_id": imdb_id}
            else:
                # Otherwise search by title and year
                params = {
                    "query_term": title,
                    "year": year
                }

            response = requests.get(
                f"{TorrentService.YTS_API_BASE}/list_movies.json",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if data["status"] != "ok" or not data["data"]["movies"]:
                return []

            movie = data["data"]["movies"][0]
            return [{
                "quality": torrent["quality"],
                "type": torrent["type"],
                "size": torrent["size"],
                "magnet_link": TorrentService._create_magnet_link(
                    torrent["hash"],
                    f"{movie['title']} {torrent['quality']}"
                )
            } for torrent in movie["torrents"]]

        except Exception as e:
            logger.error(f"Error searching for torrents: {str(e)}")
            return []

    @staticmethod
    def _create_magnet_link(hash: str, title: str) -> str:
        """Create a magnet link from a torrent hash"""
        trackers = [
            "udp://open.demonii.com:1337/announce",
            "udp://tracker.openbittorrent.com:80",
            "udp://tracker.coppersurfer.tk:6969",
            "udp://glotorrents.pw:6969/announce",
            "udp://tracker.opentrackr.org:1337/announce",
            "udp://torrent.gresille.org:80/announce",
            "udp://p4p.arenabg.com:1337",
            "udp://tracker.leechers-paradise.org:6969"
        ]

        tracker_params = "&".join(f"tr={tracker}" for tracker in trackers)
        return f"magnet:?xt=urn:btih:{hash}&dn={title}&{tracker_params}" 