import logging
from typing import List, Dict, Optional
import py1337x
from py1337x import sort, category

logger = logging.getLogger(__name__)

class TorrentService:
    def __init__(self):
        self.torrents = py1337x.Py1337x()

    @staticmethod
    def search_movie_torrents(imdb_id: str = None, title: str = None, year: int = None) -> List[Dict]:
        """
        Search for movie torrents using 1337x API
        Returns a list of available torrents with quality and size information
        """
        try:
            torrents = py1337x.Py1337x()
            search_term = title
            if year:
                search_term = f"{title} {year}"

            # Search in movies category and sort by seeders
            results = torrents.search(search_term, category=category.MOVIES, sort_by=sort.SEEDERS)
            
            if not results or not results.items:
                return []

            # Get detailed info for each torrent
            torrent_list = []
            for item in results.items[:5]:  # Limit to top 5 results
                try:
                    info = torrents.info(torrent_id=item.torrent_id)
                    # Try to determine quality from title
                    quality = "Unknown"
                    if "2160p" in info.name or "4K" in info.name:
                        quality = "2160p"
                    elif "1080p" in info.name:
                        quality = "1080p"
                    elif "720p" in info.name:
                        quality = "720p"
                    
                    torrent_list.append({
                        "quality": quality,
                        "type": "BluRay" if "BluRay" in info.name else "Web",
                        "size": info.size,
                        "magnet_link": info.magnet_link,
                        "seeders": item.seeders,
                        "name": info.name
                    })
                except Exception as e:
                    logger.error(f"Error getting torrent info: {str(e)}")
                    continue

            return sorted(torrent_list, key=lambda x: x["seeders"], reverse=True)

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