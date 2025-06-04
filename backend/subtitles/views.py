from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from movies.models import MovieFile
from .models import Subtitle
from .serializers import SubtitleSerializer
from rest_framework.pagination import PageNumberPagination
from .services import SubtitleService


class SubtitleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for subtitles operations.
    GET /subtitles - Get available subtitles with the movie id and language
    """

    queryset = Subtitle.objects.all()
    serializer_class = SubtitleSerializer
    subtitle_service = SubtitleService()

    pagination_class = PageNumberPagination
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        """
        Get subtitles for a specific movie in the user's preferred language.
        Returns a list of subtitle URLs and metadata.
        """
        movie_id = request.query_params.get("movie_id")
        language = request.query_params.get("language", request.user.preferred_language)

        if not movie_id:
            return Response({"error": "movie_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            movie = MovieFile.objects.get(tmdb_id=movie_id)
        except MovieFile.DoesNotExist:
            return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)

        subtitles = self.subtitle_service.fetch_subtitles(movie, language)
        return Response(subtitles)
