"""Semantic similarity search using pgvector and Amazon Bedrock."""
import uuid
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.bedrock import generate_embedding


async def _keyword_fallback_posts(
    db: AsyncSession,
    query_text: str,
    limit: int,
) -> list[dict]:
    terms = [t for t in re.split(r"\W+", query_text.lower()) if len(t) >= 4][:5]
    if not terms:
        return []

    like_clauses = []
    params: dict[str, object] = {"limit": limit}
    for index, term in enumerate(terms):
        key = f"term_{index}"
        params[key] = f"%{term}%"
        like_clauses.append(f"LOWER(title) LIKE :{key}")

    stmt = text(f"""
        SELECT post_id, title
        FROM posts
        WHERE {" OR ".join(like_clauses)}
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    result = await db.execute(stmt, params)
    return [
        {
            "post_id": row.post_id,
            "title": row.title,
            "similarity": 0.55,
        }
        for row in result.fetchall()
    ]


async def find_similar_posts(
    db: AsyncSession,
    query_text: str,
    exclude_post_id: uuid.UUID | None = None,
    limit: int = 5,
    min_similarity: float = 0.65,
) -> list[dict]:
    """
    Generates an embedding for query_text and finds the top `limit`
    most semantically similar posts using cosine distance via pgvector.
    Returns an empty list if Bedrock is unavailable or no matches found.
    """
    embedding = await generate_embedding(query_text)
    if embedding is None:
        return await _keyword_fallback_posts(db, query_text, limit)

    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    if exclude_post_id:
        stmt = text("""
            SELECT post_id, title, 1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM posts
            WHERE embedding IS NOT NULL
              AND post_id != CAST(:exclude_id AS uuid)
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)
        params = {"embedding": embedding_str, "exclude_id": str(exclude_post_id), "limit": limit}
    else:
        stmt = text("""
            SELECT post_id, title, 1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM posts
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)
        params = {"embedding": embedding_str, "limit": limit}

    result = await db.execute(stmt, params)

    results = [
        {
            "post_id": row.post_id,
            "title": row.title,
            "similarity": round(float(row.similarity), 3),
        }
        for row in result.fetchall()
        if float(row.similarity) >= min_similarity
    ]
    if results:
        return results
    return await _keyword_fallback_posts(db, query_text, limit)
