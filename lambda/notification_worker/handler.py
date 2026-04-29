"""
Lambda function: consumes SQS notifications queue,
writes to RDS, and optionally sends email via SES.
"""
import json
import os
import uuid
from datetime import datetime

import boto3
import psycopg2

ses = boto3.client("ses")


def get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def handler(event, context):
    conn = get_db_connection()
    cursor = conn.cursor()
    failures = []

    try:
        for record in event.get("Records", []):
            try:
                body = json.loads(record["body"])
                source_event_id = body.get("event_id")
                event_type = body.get("event_type") or body.get("type")

                cursor.execute(
                    """
                    INSERT INTO notifications
                        (
                            notification_id,
                            user_id,
                            type,
                            reference_id,
                            message,
                            source_event_id,
                            delivery_source,
                            is_read,
                            created_at
                        )
                    VALUES (%s, %s, %s, %s, %s, %s, 'sqs', FALSE, %s)
                    ON CONFLICT (source_event_id) DO NOTHING
                    """,
                    (
                        str(uuid.uuid4()),
                        body["recipient_id"],
                        event_type,
                        body["reference_id"],
                        body["message"],
                        source_event_id,
                        datetime.utcnow(),
                    ),
                )

                if body.get("send_email") and body.get("recipient_email"):
                    ses.send_email(
                        Source=os.environ.get("SENDER_EMAIL", "noreply@smartqna.example.com"),
                        Destination={"ToAddresses": [body["recipient_email"]]},
                        Message={
                            "Subject": {"Data": f"Smart Q&A: {body['message']}"},
                            "Body": {"Text": {"Data": body["message"]}},
                        },
                    )
            except Exception:
                failures.append({"itemIdentifier": record.get("messageId", "")})

        conn.commit()
        return {
            "statusCode": 200,
            "processed": len(event.get("Records", [])) - len(failures),
            "batchItemFailures": failures,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
