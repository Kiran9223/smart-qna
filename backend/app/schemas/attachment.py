import uuid
from datetime import datetime
from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    attachment_id: uuid.UUID
    filename: str
    url: str
    content_type: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}
