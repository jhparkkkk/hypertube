from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
import logging
from rest_framework.pagination import PageNumberPagination
from .services import TMDBService, TorrentService
import requests
from .models import MovieFile

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
        genre = request.query_params.get("genre", "")
        year = request.query_params.get("year", "")
        rating = request.query_params.get("rating", "")
        genre_ids = {
            "Action": 28,
            "Adventure": 12,
            "Animation": 16,
            "Comedy": 35,
            "Crime": 80,
            "Documentary": 99,
            "Drama": 18,
            "Family": 10751,
            "Fantasy": 14,
            "History": 36,
            "Horror": 27,
            "Music": 10402,
            "Mystery": 9648,
            "Romance": 10749,
            "Science Fiction": 878,
            "TV Movie": 10770,
            "Thriller": 53,
            "War": 10752,
            "Western": 37,
        }

        try:
            page = int(page)
        except ValueError:
            page = 1

        PAGE_SIZE = 20
        start_index = (page - 1) * PAGE_SIZE
        filtered_results = []
        seen_ids = set()
        tmdb_page = 1
        total_pages = 1
        total_filtered = 0

        while len(filtered_results) < (start_index + PAGE_SIZE):
            if search_query:
                data = TMDBService.search_movies(search_query, tmdb_page, language)
            else:
                data = TMDBService.get_popular_movies(tmdb_page, language)

            total_pages = data.get("total_pages", 1)

            for movie in data.get("results", []):
                if movie.get("adult", False) or not movie.get("poster_path"):
                    continue
                if genre and genre_ids.get(genre) not in movie.get("genre_ids", []):
                    continue
                if year and movie.get("release_date", "")[:4] != year:
                    continue
                if rating and movie.get("vote_average", 0) < float(rating):
                    continue
                if movie.get("id") in seen_ids:
                    continue
                seen_ids.add(movie.get("id"))
                filtered_results.append(movie)
                total_filtered += 1
                if len(filtered_results) >= (start_index + PAGE_SIZE):
                    break

            if tmdb_page >= total_pages:
                break
            tmdb_page += 1

        page_results = filtered_results[start_index : start_index + PAGE_SIZE]

        return Response(
            {
                "results": page_results,
                "page": page,
                "total_pages": total_pages,
                "total_results": total_filtered,
            }
        )

    def retrieve(self, request, pk=None):
        """Get detailed movie information and available torrents"""
        movie = self.get_tmdb_movie_details(pk)
        if not movie:
            return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)

        logger.info(f"Fetching details for movie: {movie['title']} ({pk})")

        try:
            external_ids = requests.get(
                f"{TMDBService.BASE_URL}/movie/{pk}/external_ids", headers=TMDBService.get_headers()
            ).json()
            movie["imdb_id"] = external_ids.get("imdb_id")
            logger.info(f"Got external IDs for movie: {external_ids}")
        except requests.RequestException as e:
            logger.error(f"Error fetching external IDs: {str(e)}")

        response_data = {
            "id": movie["id"],
            "title": movie["title"],
            "original_title": movie["original_title"],
            "imdb_id": movie["imdb_id"],
            "release_date": movie["release_date"],
            "runtime": movie["runtime"],
            "available_subtitles": movie["available_subtitles"],
            "comments_count": movie["comments_count"],
            "vote_average": movie["vote_average"],
            "adult": movie["adult"],
            "backdrop_path": movie["backdrop_path"],
            "belongs_to_collection": movie["belongs_to_collection"],
            "budget": movie["budget"],
            "genres": movie["genres"],
            "homepage": movie["homepage"],
            "original_language": movie["original_language"],
            "overview": movie["overview"],
            "popularity": movie["popularity"],
            "poster_path": movie["poster_path"],
            "production_companies": movie["production_companies"],
            "production_countries": movie["production_countries"],
            "revenue": movie["revenue"],
            "spoken_languages": movie["spoken_languages"],
            "status": movie["status"],
            "tagline": movie["tagline"],
            "video": movie["video"],
            "vote_count": movie["vote_count"],
        }

        # Search for available torrents
        search_params = {
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
                response_data["magnet_link"] = best_torrent["magnet"]
                response_data["available_torrents"] = best_torrents[:5]
                response_data["best_torrent"] = best_torrent
            else:
                response_data["magnet_link"] = None
                response_data["available_torrents"] = []
                response_data["best_torrent"] = None
                logger.warning("No suitable torrents found")
        else:
            response_data["available_torrents"] = []
            response_data["best_torrent"] = None
            response_data["magnet_link"] = None
            logger.warning("No suitable torrents found")

        logger.info(
            f"Returning movie details with {len(response_data.get('available_torrents', []))} available torrents"
        )
        return Response(response_data)
