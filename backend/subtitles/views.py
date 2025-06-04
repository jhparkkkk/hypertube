from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import HttpResponse, Http404
from django.conf import settings
from movies.models import MovieFile
from .models import Subtitle
from .serializers import SubtitleSerializer
from rest_framework.pagination import PageNumberPagination
from .services import SubtitleService
import os


class SubtitleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for subtitles operations.
    GET /subtitles - Get available subtitles with the movie id and language
    GET /subtitles/{movie_id}/file/{language}/ - Serve the subtitle VTT file
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

    @action(detail=False, methods=['get'], url_path=r'(?P<movie_id>\d+)/file/(?P<language>\w+)')
    def serve_file(self, request, movie_id=None, language=None):
        """
        Serve the subtitle VTT file for a specific movie and language.
        """
        if not movie_id or not language:
            raise Http404("Movie ID and language are required")

        # Construct the file path
        file_path = os.path.join(settings.MEDIA_ROOT, 'downloads', 'subtitles', movie_id, f'{language}.vtt')
        
        if not os.path.exists(file_path):
            raise Http404("Subtitle file not found")

        try:
            with open(file_path, 'r', encoding='utf-8') as subtitle_file:
                content = subtitle_file.read()
            
            response = HttpResponse(content, content_type='text/vtt')
            response['Content-Disposition'] = f'inline; filename="{language}.vtt"'
            return response
        except Exception as e:
            raise Http404(f"Error serving subtitle file: {str(e)}")
