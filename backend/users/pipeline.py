from rest_framework_simplejwt.tokens import RefreshToken
from social_core.exceptions import AuthException
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

User = get_user_model()


def associate_by_email(strategy, details, backend, user=None, *args, **kwargs):
    email = details.get("email")
    if not email:
        raise AuthException(backend, "Email is required.")

    try:
        existing_user = User.objects.get(email=email)

        if existing_user.auth_provider != backend.name:
            return redirect("/error?message=This email is already linked to another account.")

        return {"user": existing_user}

    except User.DoesNotExist:
        return None


def set_auth_provider(strategy, details, backend, user=None, *args, **kwargs):
    """
    Set the auth provider to the current to prevent duplicate accounts.
    """
    if user:
        provider = backend.name
        user.profile_picture = details.get("profile_picture")

        if user.auth_provider != provider:
            user.auth_provider = provider
            user.save()


def enforce_unique_auth_provider(strategy, backend, user=None, *args, **kwargs):
    if user:
        expected_provider = user.auth_provider
        current_provider = backend.name

        if expected_provider != current_provider:
            raise AuthException(
                backend,
                f"This account has been created with {expected_provider}. Vous ne pouvez pas vous connecter avec {current_provider}."
            )


def set_profile_picture(strategy, details, backend, user=None, response=None, *args, **kwargs):
    if user and response:
        profile_picture = response.get("avatar_url")
        if not profile_picture and backend.name == "fortytwo":
            profile_picture = response.get("image", {}).get("link")

        if profile_picture:
            user.profile_picture = profile_picture
            user.save()


def generate_jwt_and_redirect(strategy, backend, user, *args, **kwargs):
    if not user or not user.is_authenticated:
        return

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return redirect(f"http://localhost:3000/oauth-callback?access_token={access_token}&user_id={user.id}")
