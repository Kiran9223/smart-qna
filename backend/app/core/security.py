import jwt
import httpx
from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    response = httpx.get(settings.cognito_jwks_url)
    response.raise_for_status()
    return response.json()


def decode_cognito_token(token: str) -> dict:
    jwks = _get_jwks()
    header = jwt.get_unverified_header(token)
    key = next(
        (k for k in jwks["keys"] if k["kid"] == header["kid"]),
        None,
    )
    if not key:
        raise ValueError("Public key not found for token")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

    # Access tokens don't carry an 'aud' claim — skip audience validation
    claims = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        options={"verify_aud": False},
    )

    # Manually verify this is an access token issued for our app
    if claims.get("token_use") != "access":
        raise ValueError("Expected an access token")
    if claims.get("client_id") != settings.COGNITO_APP_CLIENT_ID:
        raise ValueError("Token client_id mismatch")

    return claims
