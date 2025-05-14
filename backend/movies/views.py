from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
import logging
from rest_framework.pagination import PageNumberPagination
from .services import TMDBService, TorrentService
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class MovieViewSet(viewsets.ViewSet):
    """
    ViewSet for movie operations using TMDB API.
    GET /movies - List popular movies or search by query
    GET /movies/:id - Detailed movie info
    """

    pagination_class = PageNumberPagination
    permission_classes = [permissions.AllowAny]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.torrent_service = TorrentService()

    def get_tmdb_movie_details(self, movie_id):
        """Get detailed information for a movie from TMDB"""
        return TMDBService.get_movie_details(movie_id)

    def list(self, request):
        """
        List popular movies or search by query
        """
        page = request.query_params.get("page", "1")
        search_query = request.query_params.get("query", "")
        language = request.query_params.get("language", "en-US")

        try:
            page = int(page)
        except ValueError:
            page = 1

        if search_query:
            data = TMDBService.search_movies(search_query, page, language)
        else:
            data = TMDBService.get_popular_movies(page, language)
        filtered_results = [
            movie for movie in data.get("results", []) if not movie.get("adult", False) and movie.get("poster_path")
        ]
        return Response(
            {
                "results": filtered_results,
                "page": data.get("page", 1),
                "total_pages": data.get("total_pages", 1),
                "total_results": len(filtered_results),
            }
        )

    def retrieve(self, request, pk=None):
        """Get detailed movie information and available torrents"""
        movie = self.get_tmdb_movie_details(pk)
        if not movie:
            return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)

        logger.info(f"Fetching details for movie: {movie['title']} ({pk})")

        # Get IMDB ID from TMDB for better torrent search
        try:
            external_ids = requests.get(
                f"https://api.themoviedb.org/3/movie/{pk}/external_ids", params={"api_key": settings.TMDB_API_KEY}
            ).json()
            tmdb_id = external_ids.get("tmdb_id")
            logger.info(f"Got external IDs for movie: {external_ids}")
        except requests.RequestException as e:
            logger.error(f"Error fetching external IDs: {str(e)}")
            tmdb_id = None

        # Search for available torrents
        search_params = {
            "tmdb_id": tmdb_id,
            "title": movie["title"],
            "year": int(movie["release_date"][:4]) if movie.get("release_date") else None,
        }
        logger.info(f"Searching torrents with params: {search_params}")

        torrents = self.torrent_service.search_movie_torrents(**search_params)
        logger.info(f"Found {len(torrents)} torrents")

        if torrents:
            # Sort torrents by quality and seeders
            def get_quality_score(title):
                title = title.lower()
                if "1080p" in title or "fhd" in title:
                    return 3
                elif "720p" in title or "hd" in title:
                    return 2
                elif "480p" in title or "sd" in title:
                    return 1
                return 0  # unknown quality

            # First sort by seeders to ensure reliability
            sorted_by_seeders = sorted(torrents, key=lambda t: t["seeders"], reverse=True)

            # Get top 25% of torrents with most seeders, minimum 1
            top_seeded_count = max(1, len(sorted_by_seeders) // 4)
            top_seeded = sorted_by_seeders[:top_seeded_count]

            # From the top seeded torrents, sort by quality and seeders
            best_torrents = sorted(
                top_seeded,
                key=lambda t: (
                    get_quality_score(t["title"]),  # First by quality
                    t["seeders"],  # Then by number of seeders
                    -t["size"],  # Then prefer smaller size
                ),
                reverse=True,
            )

            if best_torrents:
                best_torrent = best_torrents[0]
                logger.info(
                    "Selected torrent - Title: %s, Seeders: %d, Size: %.2f GB, Quality Score: %d",
                    best_torrent["title"],
                    best_torrent["seeders"],
                    best_torrent["size"] / (1024 * 1024 * 1024),  # Convert to GB
                    get_quality_score(best_torrent["title"]),
                )
                movie["magnet_link"] = best_torrent["magnet"]
                movie["available_torrents"] = best_torrents[:5]
                movie["best_torrent"] = best_torrent
            else:
                movie["magnet_link"] = None
                movie["available_torrents"] = []
                movie["best_torrent"] = None
                logger.warning("No suitable torrents found")
        else:
            movie["available_torrents"] = []
            movie["best_torrent"] = None
            movie["magnet_link"] = None
            logger.warning("No suitable torrents found")

        logger.info(f"Returning movie details with {len(movie.get('available_torrents', []))} available torrents")
        return Response(movie)
