from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Comment
from .serializers import CommentSerializer
from movies.models import MovieFile


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def comments_list_create(request):
    if request.method == "GET":
        comments = Comment.objects.select_related(
            "user").order_by("-created_at")
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    if request.method == "POST":
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=401)

        movie_id = request.data.get("movie_id")
        content = request.data.get("content")

        if not movie_id or not content:
            return Response({"error": "movie_id and content are required"}, status=400)

        movie = get_object_or_404(MovieFile, id=movie_id)
        comment = Comment.objects.create(
            user=request.user, movie=movie, content=content)
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=201)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def comment_detail(request, id):
    comment = get_object_or_404(Comment, id=id)

    if request.method == "GET":
        serializer = CommentSerializer(comment)
        return Response(serializer.data)

    if not request.user.is_authenticated or comment.user != request.user:
        return Response({"error": "Permission denied"}, status=403)

    if request.method == "PATCH":
        content = request.data.get("content")
        if not content:
            return Response({"error": "content is required"}, status=400)
        comment.content = content
        comment.save()
        serializer = CommentSerializer(comment)
        return Response(serializer.data)

    if request.method == "DELETE":
        comment.delete()
        return Response({"success": "Comment deleted"}, status=200)


@api_view(["GET"])
@permission_classes([AllowAny])
def movie_comments(request, movie_id):
    comments = Comment.objects.filter(movie__id=movie_id).select_related(
        "user").order_by("-created_at")
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)
