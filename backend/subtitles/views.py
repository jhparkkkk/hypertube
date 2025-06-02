from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from movies.models import MovieFile
from .models import Subtitle
from .serializers import SubtitleSerializer
from .services import SubtitleService


class SubtitleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subtitle.objects.all()
    serializer_class = SubtitleSerializer
    permission_classes = [IsAuthenticated]
    subtitle_service = SubtitleService()

    @action(detail=False, methods=['get'])
    def movie_subtitles(self, request):
        """
        Get subtitles for a specific movie in the user's preferred language.
        """
        movie_id = request.query_params.get('movie_id')
        language = request.query_params.get('language', request.user.preferred_language)

        if not movie_id:
            return Response(
                {'error': 'movie_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            movie = MovieFile.objects.get(id=movie_id)
        except MovieFile.DoesNotExist:
            return Response(
                {'error': 'Movie not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # First, try to get cached subtitles from the database
        subtitles = Subtitle.objects.filter(movie=movie, language=language)

        # If no subtitles found in the database, fetch from OpenSubtitles API
        if not subtitles.exists():
            subtitles = self.subtitle_service.fetch_subtitles(movie, language)

        serializer = self.serializer_class(subtitles, many=True)
        return Response(serializer.data)
