import json
import uuid
import re
from datetime import datetime, timezone

import boto3
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.notification import Notification
from app.schemas.notification_event import NotificationEvent, NotificationEventType

_SQS_URL_REGION_RE = re.compile(r"^https://sqs\.([a-z0-9-]+)\.amazonaws\.com/")
_sqs_clients_by_region: dict[str, object] = {}


def _resolve_sqs_region(queue_url: str | None) -> str:
    if queue_url:
        match = _SQS_URL_REGION_RE.match(queue_url.strip())
        if match:
            return match.group(1)
    return settings.AWS_REGION


def _get_sqs_client(queue_url: str | None):
    region = _resolve_sqs_region(queue_url)
    if region not in _sqs_clients_by_region:
        _sqs_clients_by_region[region] = boto3.client("sqs", region_name=region)
    return _sqs_clients_by_region[region]


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
        queue_url = settings.SQS_NOTIFICATION_QUEUE_URL
        sqs = _get_sqs_client(queue_url)
        sqs.send_message(
            QueueUrl=queue_url,
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
