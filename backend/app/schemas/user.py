import uuid
from datetime import datetime
from pydantic import BaseModel


class UserResponse(BaseModel):
    user_id: uuid.UUID
    cognito_sub: str
    email: str
    display_name: str
    avatar_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
