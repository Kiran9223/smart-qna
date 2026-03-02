from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()


class ProfileSync(BaseModel):
    email: str
    display_name: str


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def sync_profile(
    data: ProfileSync,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Called by frontend after login to sync real email/name from Cognito ID Token."""
    if data.email and "@" in data.email:
        current_user.email = data.email
    if data.display_name and data.display_name != "User":
        current_user.display_name = data.display_name
    await db.commit()
    await db.refresh(current_user)
    return current_user
