import json
import os
from urllib.request import urlopen

import psycopg2
from jose import jwt
from jose.exceptions import JWTError

_jwks_cache = None


def _json_response(status_code: int, payload: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def _load_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        region = os.environ["COGNITO_REGION"]
        pool_id = os.environ["COGNITO_USER_POOL_ID"]
        url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"
        with urlopen(url, timeout=10) as response:
            _jwks_cache = json.loads(response.read().decode("utf-8"))
    return _jwks_cache


def _decode_token(auth_header: str) -> dict:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise ValueError("Missing bearer token")

    token = auth_header.split(" ", 1)[1]
    unverified = jwt.get_unverified_header(token)
    key_id = unverified.get("kid")
    jwks = _load_jwks()

    matching_key = None
    for key in jwks.get("keys", []):
        if key.get("kid") == key_id:
            matching_key = key
            break
    if not matching_key:
        raise ValueError("Signing key not found")

    region = os.environ["COGNITO_REGION"]
    pool_id = os.environ["COGNITO_USER_POOL_ID"]
    issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
    claims = jwt.decode(
        token,
        matching_key,
        algorithms=["RS256"],
        issuer=issuer,
        options={"verify_aud": False},
    )

    app_client_id = os.environ.get("COGNITO_APP_CLIENT_ID", "")
    token_client_id = claims.get("client_id") or claims.get("aud")
    if app_client_id and token_client_id and token_client_id != app_client_id:
        raise ValueError("Token client mismatch")

    sub = claims.get("sub")
    if not sub:
        raise ValueError("Invalid token subject")
    return claims


def _resolve_user_id(claims: dict, cursor) -> str:
    sub = claims["sub"]
    cursor.execute("SELECT user_id::text FROM users WHERE cognito_sub = %s", (sub,))
    row = cursor.fetchone()
    if not row:
        raise ValueError("User not found for token")
    return row[0]


def _list_notifications(cursor, user_id: str, query: dict) -> list[dict]:
    unread_only = str(query.get("unread_only", "false")).lower() == "true"
    page = max(int(query.get("page", "1")), 1)
    size = min(max(int(query.get("size", "20")), 1), 100)
    offset = (page - 1) * size

    sql = """
        SELECT
            notification_id::text,
            type,
            reference_id::text,
            message,
            COALESCE(delivery_source, 'direct') AS delivery_source,
            is_read,
            created_at
        FROM notifications
        WHERE user_id = %s
    """
    params = [user_id]
    if unread_only:
        sql += " AND is_read = FALSE"
    sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([size, offset])

    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    return [
        {
            "notification_id": row[0],
            "type": row[1],
            "reference_id": row[2],
            "message": row[3],
            "delivery_source": row[4],
            "is_read": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
        }
        for row in rows
    ]


def _get_unread_count(cursor, user_id: str) -> int:
    cursor.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id = %s AND is_read = FALSE",
        (user_id,),
    )
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def _mark_read(cursor, user_id: str, body: dict) -> None:
    ids = body.get("notification_ids", [])
    if not ids:
        return
    cursor.execute(
        """
        UPDATE notifications
        SET is_read = TRUE
        WHERE user_id = %s
          AND notification_id = ANY(%s::uuid[])
        """,
        (user_id, ids),
    )


def handler(event, context):
    try:
        headers = event.get("headers", {}) or {}
        auth_header = headers.get("authorization") or headers.get("Authorization")
        claims = _decode_token(auth_header)
    except (ValueError, JWTError):
        return _json_response(401, {"detail": "Invalid or expired token"})

    conn = _get_db_connection()
    cursor = conn.cursor()
    try:
        user_id = _resolve_user_id(claims, cursor)
        method = event.get("requestContext", {}).get("http", {}).get("method", "")
        path = event.get("rawPath", "")
        query = event.get("queryStringParameters") or {}

        if method == "GET" and path.endswith("/notifications"):
            items = _list_notifications(cursor, user_id, query)
            return _json_response(200, items)

        if method == "GET" and path.endswith("/notifications/unread-count"):
            count = _get_unread_count(cursor, user_id)
            return _json_response(200, {"count": count})

        if method == "POST" and path.endswith("/notifications/read"):
            body = json.loads(event.get("body") or "{}")
            _mark_read(cursor, user_id, body)
            conn.commit()
            return _json_response(200, {"detail": "Marked as read"})

        return _json_response(404, {"detail": "Not found"})
    finally:
        cursor.close()
        conn.close()
