import json
import uuid
from datetime import datetime, timezone

import boto3
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.notification import Notification
from app.schemas.notification_event import NotificationEvent, NotificationEventType

sqs = boto3.client("sqs", region_name=settings.AWS_REGION)


async def notify(
    db: AsyncSession,
    recipient_id: uuid.UUID,
    type: str,
    reference_id: uuid.UUID,
    message: str,
):
    """Publish notification event to SQS (or direct-write fallback)."""
    event = NotificationEvent(
        event_type=NotificationEventType(type),
        recipient_id=recipient_id,
        reference_id=reference_id,
        message=message,
    )

    delivery_mode = (settings.NOTIFICATION_DELIVERY_MODE or "auto").lower()
    use_sqs = False

    if delivery_mode == "sqs":
        use_sqs = bool(settings.SQS_NOTIFICATION_QUEUE_URL)
    elif delivery_mode == "direct":
        use_sqs = False
    else:
        use_sqs = bool(settings.SQS_NOTIFICATION_QUEUE_URL)

    if use_sqs:
        sqs.send_message(
            QueueUrl=settings.SQS_NOTIFICATION_QUEUE_URL,
            MessageBody=event.model_dump_json(),
        )
        return

    # Local fallback for development if queue is not configured.
    notification = Notification(
        user_id=recipient_id,
        type=type,
        reference_id=reference_id,
        message=message,
        source_event_id=str(event.event_id),
        delivery_source="direct",
        created_at=datetime.now(timezone.utc),
    )
    db.add(notification)
    await db.flush()
