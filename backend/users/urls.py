from django.urls import path, include
from .views import create_user, update_user, oauth_token, oauth_success, get_me, users, request_reset_password, reset_password, delete_user

urlpatterns = [
    path("", include("social_django.urls", namespace="social")),
    path("register", create_user, name="register"),
    path("oauth/token", oauth_token, name="login"),
    path("oauth/success/", oauth_success, name="oauth-success"),
    path("users/me/", get_me, name="user-me"),
    path("users/", users, name="users"),
    path("users/<int:id>/", users, name="users"),
    path("request-reset-password", request_reset_password, name="reset-password"),
    path("reset-password/<str:token>/",
         reset_password, name="reset-password"),
    path("delete-user", delete_user, name="delete-user"),
    path("update-user", update_user, name="update-user"),
]
