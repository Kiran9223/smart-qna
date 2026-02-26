import uuid
from sqlalchemy import select, func, desc
from app.models.post import Post
from app.models.tag import Tag


def build_post_query(
    search: str | None = None,
    tag: str | None = None,
    sort: str = "latest",
    author_id: str | None = None,
):
    query = select(Post)

    if search:
        ts_query = func.plainto_tsquery("english", search)
        query = query.where(Post.search_vector.op("@@")(ts_query))
        query = query.order_by(desc(func.ts_rank(Post.search_vector, ts_query)))
    elif sort == "latest":
        query = query.order_by(desc(Post.created_at))
    elif sort == "unanswered":
        query = query.where(Post.answer_count == 0).order_by(desc(Post.created_at))
    elif sort == "popular":
        query = query.order_by(desc(Post.vote_count), desc(Post.created_at))

    if tag:
        query = query.join(Post.tags).where(Tag.name == tag)

    if author_id:
        query = query.where(Post.author_id == author_id)

    # Pinned posts always appear first
    query = query.order_by(desc(Post.is_pinned))

    return query
