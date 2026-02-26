"""AWS Cognito JWT validation — replaces core/security.py in production."""
import httpx
from jose import jwt, jwk, JWTError
from app.config import settings

JWKS_URL = (
    f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com"
    f"/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)

_jwks_cache = None


async def get_jwks():
    global _jwks_cache
    if not _jwks_cache:
        async with httpx.AsyncClient() as client:
            resp = await client.get(JWKS_URL)
            _jwks_cache = resp.json()["keys"]
    return _jwks_cache


async def decode_cognito_token(token: str) -> dict:
    keys = await get_jwks()
    header = jwt.get_unverified_header(token)
    key = next((k for k in keys if k["kid"] == header["kid"]), None)
    if not key:
        raise JWTError("Key not found")
    public_key = jwk.construct(key)
    payload = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=settings.COGNITO_APP_CLIENT_ID,
        issuer=(
            f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com"
            f"/{settings.COGNITO_USER_POOL_ID}"
        ),
    )
    return payload
