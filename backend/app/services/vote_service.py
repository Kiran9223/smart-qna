import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.vote import Vote
from app.models.post import Post
from app.models.answer import Answer


async def toggle_post_vote(db: AsyncSession, user_id: uuid.UUID, post_id: uuid.UUID, vote_type: str):
    result = await db.execute(
        select(Vote).where(Vote.post_id == post_id, Vote.user_id == user_id)
    )
    existing = result.scalar_one_or_none()

    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if existing is None:
        db.add(Vote(post_id=post_id, user_id=user_id, vote_type=vote_type))
        post.vote_count += 1 if vote_type == "UP" else -1
        user_vote = vote_type
    elif existing.vote_type == vote_type:
        await db.delete(existing)
        post.vote_count -= 1 if vote_type == "UP" else -1
        user_vote = None
    else:
        existing.vote_type = vote_type
        post.vote_count += 2 if vote_type == "UP" else -2
        user_vote = vote_type

    await db.flush()
    return {"vote_count": post.vote_count, "user_vote": user_vote}


async def toggle_answer_vote(db: AsyncSession, user_id: uuid.UUID, answer_id: uuid.UUID, vote_type: str):
    result = await db.execute(
        select(Vote).where(Vote.answer_id == answer_id, Vote.user_id == user_id)
    )
    existing = result.scalar_one_or_none()

    answer = await db.get(Answer, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    if existing is None:
        db.add(Vote(answer_id=answer_id, user_id=user_id, vote_type=vote_type))
        answer.vote_count += 1 if vote_type == "UP" else -1
        user_vote = vote_type
    elif existing.vote_type == vote_type:
        await db.delete(existing)
        answer.vote_count -= 1 if vote_type == "UP" else -1
        user_vote = None
    else:
        existing.vote_type = vote_type
        answer.vote_count += 2 if vote_type == "UP" else -2
        user_vote = vote_type

    await db.flush()
    return {"vote_count": answer.vote_count, "user_vote": user_vote}
