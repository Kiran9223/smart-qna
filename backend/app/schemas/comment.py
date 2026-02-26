import uuid
from datetime import datetime
from pydantic import BaseModel
from app.schemas.user import UserResponse


class CommentCreate(BaseModel):
    body: str


class CommentResponse(BaseModel):
    comment_id: uuid.UUID
    author_id: uuid.UUID
    post_id: uuid.UUID | None = None
    answer_id: uuid.UUID | None = None
    body: str
    created_at: datetime
    author: UserResponse

    model_config = {"from_attributes": True}
