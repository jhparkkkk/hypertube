from social_core.backends.oauth import BaseOAuth2
import logging

logger = logging.getLogger(__name__)

class FortyTwoOAuth2(BaseOAuth2):
    name = "fortytwo"
    AUTHORIZATION_URL = "https://api.intra.42.fr/oauth/authorize"
    ACCESS_TOKEN_URL = "https://api.intra.42.fr/oauth/token"
    USER_DATA_URL = "https://api.intra.42.fr/v2/me"
    DEFAULT_SCOPE = ["public"]
    # TODO: handle state verification
    REDIRECT_STATE = False 
    EXTRA_DATA = [
        ("id", "id"),
        ("login", "username"),
        ("email", "email"),
        ("first_name", "first_name"),
        ("last_name", "last_name"),
    ]

    def get_user_details(self, response):
        if "login" not in response or "email" not in response:
            logger.error("Cannot fetch user data: %s", response)
            raise ValueError("Required user data is missing")

        return {
            "username": response["login"],
            "email": response["email"],
            "first_name": response.get("first_name", ""),
            "last_name": response.get("last_name", ""),
            "auth_provider": self.name,
        }

    def request_access_token(self, *args, **kwargs):
        params = kwargs.get("params", {})

        required_keys = ["client_id", "client_secret", "code", "redirect_uri"]
        for key in required_keys:
            if not params.get(key):
                logger.error("Missing OAuth2 parameter: %s", key)
                raise ValueError(f"Parameter {key} is required.")

        response = self.request(
            url=self.ACCESS_TOKEN_URL,
            method="POST",
            data={
                "grant_type": "authorization_code",
                "client_id": params["client_id"],
                "client_secret": params["client_secret"],
                "code": params["code"],
                "redirect_uri": params["redirect_uri"],
            },
            headers={"Accept": "application/json"},
        ).json()

        if "access_token" not in response:
            logger.error("Error fetching 42 access token: %s", response)
            raise ValueError("Error fetching 42 access token.")

        logger.debug("💚 Successfully retrieved access token: %s", response)
        return response

    def user_data(self, access_token, *args, **kwargs):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self.get_json(self.USER_DATA_URL, headers=headers)

        if "login" not in response or "email" not in response:
            logger.error("Cannot retrieve user data: %s", response)
            raise ValueError("User data is invalid.")

        logger.debug("💚 Successfully retrieved user data: %s", response)
        return response
