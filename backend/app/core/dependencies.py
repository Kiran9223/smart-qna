from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.core.security import decode_cognito_token
from app.models.user import User

bearer_scheme = HTTPBearer()
optional_bearer_scheme = HTTPBearer(auto_error=False)


async def _resolve_user(claims: dict, db: AsyncSession) -> User:
    """Fetch user by cognito_sub, creating a stub record on first login.
    Real email/name are filled in by PATCH /auth/me after frontend syncs."""
    sub = claims.get("sub")

    result = await db.execute(select(User).where(User.cognito_sub == sub))
    user = result.scalar_one_or_none()

    if not user:
        user = User(cognito_sub=sub, email=sub, display_name="User")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        claims = decode_cognito_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return await _resolve_user(claims, db)


async def get_current_user_with_claims(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> tuple[User, dict]:
    try:
        claims = decode_cognito_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await _resolve_user(claims, db)
    return user, claims


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not credentials:
        return None
    try:
        claims = decode_cognito_token(credentials.credentials)
        return await _resolve_user(claims, db)
    except Exception:
        return None


def require_role(*roles: str):
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        try:
            claims = decode_cognito_token(credentials.credentials)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_groups = claims.get("cognito:groups", [])
        if not any(r in user_groups for r in roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return await _resolve_user(claims, db)
    return role_checker
