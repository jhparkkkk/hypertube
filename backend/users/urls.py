from django.urls import path, include
from .views import register_user, login_user

urlpatterns = [
    path("", include("social_django.urls", namespace="social")),
    path("register/", register_user, name="register"),
    path("login/", login_user, name="login"),
]
