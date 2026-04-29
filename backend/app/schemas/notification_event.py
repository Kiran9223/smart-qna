from datetime import datetime, timezone
from enum import Enum
import uuid

from pydantic import BaseModel, Field


class NotificationEventType(str, Enum):
    ANSWER = "ANSWER"
    COMMENT = "COMMENT"
    ACCEPTED = "ACCEPTED"


class NotificationEvent(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: NotificationEventType
    event_version: int = 1
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recipient_id: uuid.UUID
    reference_id: uuid.UUID
    message: str
    recipient_email: str | None = None
    send_email: bool = False
