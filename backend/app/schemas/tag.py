import uuid
from pydantic import BaseModel


class TagResponse(BaseModel):
    tag_id: uuid.UUID
    name: str
    description: str | None = None
    post_count: int = 0

    model_config = {"from_attributes": True}


class TagBase(BaseModel):
    tag_id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}
