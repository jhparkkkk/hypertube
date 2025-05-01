from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import WatchHistory
from movies.models import MovieFile
from .serializers import WatchHistorySerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_as_watched(request, movie_id):
    movie = MovieFile.objects.filter(id=movie_id).first()
    if not movie:
        return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)

    history, created = WatchHistory.objects.get_or_create(
        user=request.user, movie=movie)
    return Response({"success": "Marked as watched"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_watch_history(request):
    history = WatchHistory.objects.filter(user=request.user)
    serializer = WatchHistorySerializer(history, many=True)
    return Response(serializer.data)
