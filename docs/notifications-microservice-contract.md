# Notifications Microservice Contract

## Event Contract (Core Backend -> SQS)

JSON payload:

- `event_id` (UUID)
- `event_type` (`ANSWER` | `COMMENT` | `ACCEPTED`)
- `event_version` (integer, currently `1`)
- `occurred_at` (ISO-8601 timestamp)
- `recipient_id` (UUID)
- `reference_id` (UUID)
- `message` (string)
- `recipient_email` (optional string)
- `send_email` (optional boolean)

## Notification API Contract

Base URL is provided via frontend env `VITE_NOTIFICATION_API_URL`.

- `GET /notifications?unread_only={bool}&page={int}&size={int}`
- `GET /notifications/unread-count`
- `POST /notifications/read`
  - body: `{ "notification_ids": ["<uuid>", "..."] }`

All endpoints require `Authorization: Bearer <CognitoAccessToken>`.
