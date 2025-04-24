import logging
import sys
import requests
from typing import Dict, Any, List
from django.conf import settings
import os
from urllib.parse import quote_plus
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


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
        self.jackett_url = os.getenv("JACKETT_URL", "http://jackett:9117")
        self.api_key = os.getenv("JACKETT_API_KEY")
        if not self.api_key:
            logger.error("JACKETT_API_KEY not set in environment variables")
        self.min_seeders = 3
        self.language_names = {}
        self._init_language_names()
        # logger.info("TorrentService initialized with URL: %s", self.jackett_url)

    def _init_language_names(self):
        """Initialize language names from TMDB configuration"""
        try:
            url = "https://api.themoviedb.org/3/configuration/languages"
            headers = {"Authorization": f"Bearer {settings.TMDB_API_TOKEN}"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            for lang in response.json():
                iso = lang.get("iso_639_1")
                if iso:
                    eng_name = lang.get("english_name", "").lower()
                    native_name = lang.get("name", "").lower()

                    variations = set()
                    if eng_name:
                        variations.add(eng_name)
                        variations.add(eng_name.replace(" ", ""))
                    if native_name:
                        variations.add(native_name)
                        variations.add(native_name.replace(" ", ""))

                    variations.add(iso)

                    self.language_names[iso] = variations

            # logger.info(f"Initialized {len(self.language_names)} language mappings")
        except Exception as e:
            logger.error(f"Error initializing language names: {str(e)}")
            self.language_names = {}

    def _detect_language_in_title(self, title: str, original_language: str) -> bool:
        """
        Detect if a torrent title indicates it's in the original language
        Returns True if the title suggests original language or if we can't determine
        """
        title = title.lower()

        dubbed_patterns = {
            "es": ["latino", "latin0", "español", "castellano", "spanish"],
            "fr": ["french", "français", "vf", "truefrench", "doublage"],
            "de": ["german", "deutsch", "ger"],
            "it": ["italian", "italiano", "ita"],
            "pt": ["portuguese", "português", "dublado"],
            "ru": ["russian", "русский"],
            "ja": ["japanese", "日本語"],
            "ko": ["korean", "한국어"],
            "zh": ["chinese", "中文"],
            "general": ["dubbed", "dub", "dual", "multi"],
        }

        if not original_language:
            # logger.info("No original language info from TMDB, checking common patterns")
            all_dub_patterns = [p for patterns in dubbed_patterns.values() for p in patterns]
            if any(pattern in title for pattern in all_dub_patterns):
                # logger.info(f"Found dubbed pattern in title: {title}")
                return False
            return True

        if original_language == "en":
            all_dub_patterns = [p for patterns in dubbed_patterns.values() for p in patterns]
            if any(pattern in title for pattern in all_dub_patterns):
                # logger.info(f"Found dubbed pattern in English content: {title}")
                return False
            return True

        else:
            for lang, patterns in dubbed_patterns.items():
                if lang != original_language and any(pattern in title for pattern in patterns):
                    # logger.info(f"Found {lang} dub pattern in {original_language} content: {title}")
                    return False

            multi_patterns = ["multi", "dual", "multi-audio", "dual-audio"]
            if any(pattern in title for pattern in multi_patterns):
                # logger.info(f"Found multi-language pattern: {title}")
                return False

            if original_language in dubbed_patterns:
                if any(pattern in title for pattern in dubbed_patterns[original_language]):
                    # logger.info(f"Found original language ({original_language}) pattern: {title}")
                    return True

            # logger.info(f"No language indicators found, assuming original for: {title}")
            return True

    def _clean_title(self, title: str) -> str:
        """Clean title by removing special characters and extra spaces"""
        cleaned = re.sub(r"[^\w\s]", "", title)
        return " ".join(cleaned.split())

    def _generate_search_terms(self, title: str, year: int = None) -> List[str]:
        """Generate various formats of the title for better torrent matching"""
        terms = []

        clean_title = self._clean_title(title)

        if year:
            terms.append(f"{title} {year}")

        if year:
            terms.append(f"{clean_title} {year}")

        terms.append(title)

        if clean_title != title:
            terms.append(clean_title)

        for article in ["the ", "a ", "an "]:
            if clean_title.lower().startswith(article):
                no_article = clean_title[len(article) :].strip()
                terms.append(no_article)
                if year:
                    terms.append(f"{no_article} {year}")

        return list(dict.fromkeys(terms))

    def search_movie_torrents(self, tmdb_id: str = None, title: str = None, year: int = None) -> List[Dict]:
        """
        Search for movie torrents using Jackett API
        Returns a list of available torrents with quality and size information
        """
        try:
            # logger.info("=== Starting torrent search ===")
            original_language = None
            original_title = None

            if tmdb_id:
                try:
                    tmdb_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
                    headers = {"Authorization": f"Bearer {settings.TMDB_API_TOKEN}"}
                    movie_info = requests.get(tmdb_url, headers=headers).json()

                    original_language = movie_info.get("original_language")
                    original_title = movie_info.get("original_title")

                    # logger.info(f"TMDB info - Original language: {original_language}")
                    # logger.info(f"Original title: {original_title}")

                except Exception as e:
                    logger.error(f"Error fetching TMDB info: {str(e)}")

            search_terms = []
            if original_title and original_title != title:
                search_terms.extend(self._generate_search_terms(original_title, year))
            search_terms.extend(self._generate_search_terms(title, year))

            # logger.info(f"Generated search terms: {search_terms}")

            all_results = []
            for search_term in search_terms:
                # logger.info(f"Searching Jackett for term: {search_term}")

                search_url = f"{self.jackett_url}/api/v2.0/indexers/all/results"
                params = {
                    "apikey": self.api_key,
                    "Query": search_term,
                    "Category[]": ["2000", "2010", "2020", "2030", "2040", "2045", "2050", "2060"],
                    "Type": "search",
                }

                response = requests.get(search_url, params=params, timeout=10)

                if not response.ok:
                    logger.error(f"Jackett API error: {response.status_code} - {response.text}")
                    continue

                try:
                    current_results = response.json().get("Results", [])
                    # logger.info(f"Found {len(current_results)} results for term: {search_term}")
                    all_results.extend(current_results)
                except Exception as e:
                    logger.error(f"Failed to parse Jackett response: {str(e)}")
                    continue

            # logger.info(f"Total results found: {len(all_results)}")
            torrent_list = []
            valid_results = 0
            invalid_results = 0
            dubbed_results = 0

            for result in all_results:
                try:
                    title = result.get("Title", "Unknown")
                    # logger.info(f"\nProcessing torrent: {title}")

                    magnet_uri = result.get("MagnetUri")
                    if not magnet_uri:
                        link = result.get("Link")
                        if isinstance(link, str) and link.startswith("magnet:?"):
                            magnet_uri = link
                        else:
                            info_hash = result.get("InfoHash")
                            if info_hash:
                                magnet_uri = self._create_magnet_link(info_hash, title)
                            else:
                                # logger.info(f"Skipping torrent without magnet: {title}")
                                invalid_results += 1
                                continue

                    seeders = safe_int(result.get("Seeders"))
                    if seeders < 1:
                        # logger.info(f"Skipping torrent with no seeders: {title}")
                        invalid_results += 1
                        continue

                    # logger.info(f"Checking language for: {title}")
                    is_original = self._detect_language_in_title(title, original_language)
                    # logger.info(f"Language check result for {title}: {'original' if is_original else 'dubbed'}")

                    if not is_original:
                        # logger.info(f"Skipping dubbed version: {title}")
                        dubbed_results += 1
                        continue

                    peers = safe_int(result.get("Peers"))
                    size = safe_int(result.get("Size"))

                    torrent = {
                        "title": title,
                        "size": size,
                        "seeders": seeders,
                        "leechers": max(0, peers - seeders),
                        "magnet": magnet_uri,
                        "source": result.get("Tracker", "Unknown"),
                        "original_language": original_language,
                        "is_original": is_original,
                    }

                    valid_results += 1
                    torrent_list.append(torrent)
                    # logger.info(f"Added valid torrent: {title}")

                except Exception as e:
                    invalid_results += 1
                    logger.error(f"Error processing result: {str(e)} - {result}")
                    continue

            # Sort by quality and language match
            def get_sort_score(t):
                quality_score = 0
                title = t["title"].lower()

                # Quality scoring
                if "1080p" in title or "fhd" in title:
                    quality_score = 3
                elif "720p" in title or "hd" in title:
                    quality_score = 2
                elif "480p" in title or "sd" in title:
                    quality_score = 1

                # Prioritize original language versions
                language_score = 2 if t["is_original"] else 1

                return (language_score, quality_score, t["seeders"], -t["size"])

            torrent_list.sort(key=get_sort_score, reverse=True)

            # logger.info(f"\n=== Search complete ===")
            # logger.info(f"Valid torrents: {valid_results}")
            # logger.info(f"Invalid torrents: {invalid_results}")
            # logger.info(f"Dubbed versions skipped: {dubbed_results}")
            # logger.info(f"Total torrents found: {len(torrent_list)}")

            return torrent_list

        except requests.Timeout:
            logger.error("Timeout while connecting to Jackett")
            return []
        except requests.ConnectionError as e:
            logger.error(f"Connection error to Jackett: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error searching for torrents: {str(e)}")
            return []

    @staticmethod
    def _create_magnet_link(info_hash: str, title: str) -> str:
        """Create a magnet link from info hash and title"""
        if not info_hash:
            return ""

        trackers = get_trackers()
        encoded_title = quote_plus(title)
        tracker_params = "&".join(f"tr={quote_plus(tracker)}" for tracker in trackers)

        return f"magnet:?xt=urn:btih:{info_hash}&dn={encoded_title}&{tracker_params}"


def get_trackers():
    """Fetch trackers from GitHub repositories"""
    trackers = set()

    try:
        response = requests.get(
            "https://raw.githubusercontent.com/XIU2/TrackersListCollection/refs/heads/master/best.txt"
        )
        if response.status_code == 200:
            trackers.update(response.text.strip().split("\n"))
    except Exception as e:
        logging.error(f"Error fetching XIU2 trackers: {str(e)}")

    try:
        response = requests.get(
            "https://raw.githubusercontent.com/ngosang/trackerslist/refs/heads/master/trackers_best.txt"
        )
        if response.status_code == 200:
            trackers.update(response.text.strip().split("\n"))
    except Exception as e:
        logging.error(f"Error fetching ngosang trackers: {str(e)}")

    fallback_trackers = [
        "udp://tracker.opentrackr.org:1337/announce",
        "udp://open.demonii.com:1337/announce",
        "udp://open.stealth.si:80/announce",
        "udp://tracker.torrent.eu.org:451/announce",
        "udp://tracker.skyts.net:6969/announce",
        "udp://tracker.dump.cl:6969/announce",
        "udp://ns-1.x-fins.com:6969/announce",
        "udp://explodie.org:6969/announce",
        "udp://exodus.desync.com:6969/announce",
        "http://www.torrentsnipe.info:2701/announce",
        "http://tracker810.xyz:11450/announce",
        "http://tracker.xiaoduola.xyz:6969/announce",
        "http://tracker.sbsub.com:2710/announce",
        "http://tracker.corpscorp.online:80/announce",
        "http://tracker.bz:80/announce",
        "http://share.hkg-fansub.info:80/announce.php",
        "http://seeders-paradise.org:80/announce",
        "http://home.yxgz.club:6969/announce",
        "http://finbytes.org:80/announce.php",
        "http://buny.uk:6969/announce",
    ]

    if not trackers:
        trackers.update(fallback_trackers)

    return list(trackers)


trackers = get_trackers()


def safe_int(value, default=0):
    if not value:
        return default
    try:
        return int(str(value))
    except (ValueError, TypeError):
        return default
