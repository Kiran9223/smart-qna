from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.tag import Tag, post_tags
from app.models.post import Post
from app.schemas.tag import TagResponse
from app.schemas.post import PostListResponse
from app.services.search_service import build_post_query
from app.utils.pagination import paginate

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Tag,
            func.count(post_tags.c.post_id).label("post_count"),
        )
        .outerjoin(post_tags, Tag.tag_id == post_tags.c.tag_id)
        .group_by(Tag.tag_id)
        .order_by(Tag.name)
    )
    rows = result.all()
    return [
        TagResponse(
            tag_id=row.Tag.tag_id,
            name=row.Tag.name,
            description=row.Tag.description,
            post_count=row.post_count,
        )
        for row in rows
    ]


@router.get("/{tag_name}/posts", response_model=PostListResponse)
async def posts_by_tag(
    tag_name: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = build_post_query(tag=tag_name)
    query = query.options(selectinload(Post.author), selectinload(Post.tags))
    return await paginate(db, query, page, size)
