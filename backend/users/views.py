from django.shortcuts import render
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.hashers import make_password
from .serializers import UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def create_user(request):
    serializer = UserSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        tokens = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        return Response({
            "user": serializer.data,
            "tokens": tokens,
        }, status=status.HTTP_201_CREATED)
    print("[DEBUG] serializer.errors", serializer.errors)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def oauth_token(request):
    client_id = request.data.get("client_id")
    client_secret = request.data.get("client_secret")
    print("[DEBUG] client_id", client_id)
    print("[DEBUG] client_secret", client_secret)
    if client_id != settings.VITE_CLIENT_ID or client_secret != settings.VITE_CLIENT_SECRET:
        return Response({"error": "Invalid client_id or client_secret"}, status=status.HTTP_400_BAD)

    username = request.data.get("username")
    password = request.data.get("password")
    try:
        email = User.objects.get(username=username).email
    except User.DoesNotExist:
        return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

    user = authenticate(email=email, password=password)
    print("[DEBUG] user", user)
    if user:
        refresh = RefreshToken.for_user(user)
        tokens = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        return Response({
            "user": UserSerializer(user).data,
            "tokens": tokens,
        }, status=status.HTTP_200_OK)
    print("PROBLEMO")
    return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def users(request):
    print("[DEBUUUUUUG] request", request)
    # if request and request.id:
    # user = User.objects.get(id=request.id)
    # serializer = UserSerializer(user)
    # return Response(serializer.data, status=status
    # .HTTP_200_OK)
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
