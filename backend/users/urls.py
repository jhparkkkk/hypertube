from django.urls import path, include
from .views import create_user, oauth_token, users

urlpatterns = [
    path("", include("social_django.urls", namespace="social")),
    path("register", create_user, name="register"),
    path("oauth/token", oauth_token, name="login"),
    path("users/", users, name="users"),
]
