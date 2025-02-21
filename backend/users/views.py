from django.shortcuts import render

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import make_password
from .serializers import UserSerializer


User = get_user_model()

@api_view(["POST"])
def register_user(request):
    data = request.data
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    print("[DEBUG] serializer.errors", serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)