import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.answer import Answer
from app.models.post import Post


async def accept_answer(db: AsyncSession, answer: Answer, current_user_id: uuid.UUID):
    post = await db.get(Post, answer.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id != current_user_id:
        raise HTTPException(status_code=403, detail="Only the post author can accept an answer")

    answer.is_accepted = True
    post.status = "SOLVED"
    await db.flush()
    return answer
