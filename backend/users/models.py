from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class AuthProvider:
    EMAIL = "email"
    GITHUB = "github"
    FORTYTWO = "fortytwo"


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    password = models.CharField(max_length=128)
    profile_picture = models.URLField(max_length=500, blank=True, null=True)
    preferred_language = models.CharField(max_length=5, default="en")
    auth_provider = models.CharField(max_length=50, choices=[
        (AuthProvider.EMAIL, "Email"),
        (AuthProvider.GITHUB, "Github"),
        (AuthProvider.FORTYTWO, "fortytwo"),
    ],
        default=AuthProvider.EMAIL)
    print("[DEBUG] User model: auth_provider", auth_provider)
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} - {self.auth_provider}"


class PasswordReset(models.Model):
    email = models.EmailField()
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.token}"
