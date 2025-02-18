from social_core.exceptions import AuthException
from django.contrib.auth import get_user_model

User = get_user_model()

def associate_by_email(strategy, details, backend, user=None, *args, **kwargs):
    email = details.get("email")
    if not email:
        raise AuthException(backend, "Email is required.")

    try:
        existing_user = User.objects.get(email=email)
        
        if existing_user.auth_provider != backend.name:
            raise AuthException(
                backend,
                f"This email is already registered with {existing_user.auth_provider}. "
                "Please log in with the original provider."
            )

        return {"user": existing_user}

    except User.DoesNotExist:
        return None

def set_auth_provider(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        provider = backend.name
        if user.auth_provider != provider:
            user.auth_provider = provider
            user.save()

