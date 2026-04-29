import uuid
from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    notification_id: uuid.UUID
    type: str
    reference_id: uuid.UUID | None = None
    message: str
    delivery_source: str | None = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MarkReadRequest(BaseModel):
    notification_ids: list[uuid.UUID]


class UnreadCountResponse(BaseModel):
    count: int
