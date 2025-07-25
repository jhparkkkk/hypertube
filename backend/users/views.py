from django.shortcuts import render
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.hashers import make_password

from .serializers import UserSerializer, ResetPasswordSerializer, UserUpdateSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from users.models import PasswordReset
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.shortcuts import redirect

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

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def oauth_token(request):
    client_id = request.data.get("client_id")
    client_secret = request.data.get("client_secret")
    print("[DEBUG] client_id sent from client:", client_id)
    print("[DEBUG] client_secret sent from client", client_secret)
    if client_id != settings.VITE_CLIENT_ID or client_secret != settings.VITE_CLIENT_SECRET:
        return Response({"error": "Invalid client_id or client_secret"}, status=status.HTTP_400_BAD_REQUEST)

    username = request.data.get("username")
    password = request.data.get("password")
    try:
        email = User.objects.get(username=username).email
    except User.DoesNotExist:
        return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

    user = authenticate(email=email, password=password)
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
    return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def oauth_success(request):
    user = request.user
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    redirect_url = f"http://localhost:3000/oauth-callback?access_token={access_token}&refresh_token={refresh_token}"
    return redirect(redirect_url)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_me(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def users(request, id=None):
    if request.method == "GET":
        try:
            if id:
                user = User.objects.get(id=id)
                serializer = UserSerializer(user)
                return Response(serializer.data, status=status.HTTP_200_OK)

            # search user by username
            search = request.query_params.get("search")
            if search:
                user = User.objects.filter(username__iexact=search).first()
                if not user:
                    return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                serializer = UserSerializer(user)
                return Response(serializer.data)

            users = User.objects.all()
            serializer = UserSerializer(users, many=True)

            users_list = []
            for user in serializer.data:
                users_list.append({
                    "id": user["id"],
                    "username": user["username"],
                })
            return Response(users_list, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PATCH":
        user = User.objects.get(id=id)
        if request.user != user:
            return Response({"error": "You are not allowed this profile"}, status=status.HTTP_403_FORBIDDEN)
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def request_reset_password(request):
    email = request.data.get("email")
    if not email:
        return Response({"error": "Email is required"}, status=400)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "User with credentials not found"}, status=status.HTTP_404_NOT_FOUND)
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    reset = PasswordReset.objects.create(email=email, token=token)
    reset.save()

    reset_url = f"http://localhost:3000/reset-password/param?reset-token={token}"
    subject = 'Password Reset Request'
    message = render_to_string('password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })
    from_email = settings.EMAIL_HOST_USER
    email = EmailMessage(subject, message, from_email, [email])
    email.content_subtype = "html"
    email.send(fail_silently=False)
    return Response({"success": "We have sent you a link to reset your password"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request, token=''):
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if new_password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        reset_obj = PasswordReset.objects.get(token=token)
    except PasswordReset.DoesNotExist:
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=reset_obj.email)
    except User.DoesNotExist:
        return Response({"error": "User with email not found"}, status=status.HTTP_404_NOT_FOUND)

    user.set_password(new_password)
    user.save()
    reset_obj.delete()

    return Response({"success": "Password reset successful"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_user(request):
    user = request.user
    user.delete()
    return Response({"success": "User deleted"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_user(request):
    user = request.user
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)
