from django.contrib.auth.models import BaseUserManager
from django.db import transaction


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, auth_provider="email", **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)

        existing_user = self.model.objects.filter(email=email)
        if existing_user.exists():
            raise ValueError(f"User with email {email} is already registered with {existing_user.auth_provider}.")

        try:
            with transaction.atomic():
                user = self.model(email=email, auth_provider=auth_provider, **extra_fields)
                if password:
                    user.set_password(password)

                user.save(using=self._db)
                return user
        except Exception as e:
            raise ValueError(f"Error creating user: {e}")

    #def create_oauth_user(self, email, username, provider, profile_picture=None):
    #    return self.create_user(email=email, password=None, username=username, auth_provider=provider, profile_picture=profile_picture)
