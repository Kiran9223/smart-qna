import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.vote import VoteRequest, VoteResponse
from app.services.vote_service import toggle_post_vote, toggle_answer_vote

router = APIRouter()


@router.post("/posts/{post_id}/vote", response_model=VoteResponse)
async def vote_on_post(
    post_id: uuid.UUID,
    data: VoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await toggle_post_vote(db, current_user.user_id, post_id, data.type)


@router.post("/answers/{answer_id}/vote", response_model=VoteResponse)
async def vote_on_answer(
    answer_id: uuid.UUID,
    data: VoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await toggle_answer_vote(db, current_user.user_id, answer_id, data.type)
