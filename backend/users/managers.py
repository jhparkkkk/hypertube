from django.contrib.auth.models import BaseUserManager



class UserManager(BaseUserManager):
    def create_user(self, email, password=None, auth_provider="email", **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, auth_provider=auth_provider, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_oauth_user(self, email, username, provider, profile_picture=None):
        return self.create_user(email=email, password=None, username=username, auth_provider=provider, profile_picture=profile_picture)
