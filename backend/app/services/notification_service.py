import json
import uuid

import boto3
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.notification import Notification

sqs = boto3.client("sqs", region_name=settings.COGNITO_REGION)


async def notify(
    db: AsyncSession,
    recipient_id: uuid.UUID,
    type: str,
    reference_id: uuid.UUID,
    message: str,
):
    """
    Development/local: direct DB insert.
    Production with SQS queue URL set: publish to SQS.
    """
    if settings.ENVIRONMENT == "production" and settings.SQS_NOTIFICATION_QUEUE_URL:
        sqs.send_message(
            QueueUrl=settings.SQS_NOTIFICATION_QUEUE_URL,
            MessageBody=json.dumps(
                {
                    "recipient_id": str(recipient_id),
                    "type": type,
                    "reference_id": str(reference_id),
                    "message": message,
                }
            ),
        )
        return

    notification = Notification(
        user_id=recipient_id,
        type=type,
        reference_id=reference_id,
        message=message,
    )
    db.add(notification)
    await db.flush()