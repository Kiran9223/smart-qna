import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.dependencies import get_current_user, get_optional_user, require_role
from app.models.user import User
from app.models.post import Post
from app.models.vote import Vote
from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostDetailResponse, PostListResponse, PostSummary
from app.services.post_service import create_post, update_post, get_post_with_relations
from app.services.search_service import build_post_query
from app.utils.pagination import paginate

router = APIRouter()


@router.post("", response_model=PostResponse, status_code=201)
async def create_post_endpoint(
    data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = await create_post(db, data, current_user.user_id)
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.author), selectinload(Post.tags))
        .where(Post.post_id == post.post_id)
    )
    return result.scalar_one()


@router.get("", response_model=PostListResponse)
async def list_posts(
    sort: str = Query("latest", enum=["latest", "unanswered", "popular"]),
    tag: str | None = Query(None),
    search: str | None = Query(None),
    author_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = build_post_query(search=search, tag=tag, sort=sort, author_id=str(author_id) if author_id else None)
    query = query.options(selectinload(Post.author), selectinload(Post.tags))
    paginated = await paginate(db, query, page, size)
    return paginated


@router.get("/{post_id}", response_model=PostDetailResponse)
async def get_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    post = await get_post_with_relations(db, post_id)

    # Increment view count
    post.view_count += 1
    await db.flush()

    user_vote = None
    if current_user:
        vote_result = await db.execute(
            select(Vote).where(Vote.post_id == post_id, Vote.user_id == current_user.user_id)
        )
        vote = vote_result.scalar_one_or_none()
        user_vote = vote.vote_type if vote else None

    response = PostDetailResponse.model_validate(post)
    response.user_vote = user_vote
    return response


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_endpoint(
    post_id: uuid.UUID,
    data: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = await db.get(Post, post_id)
    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not authorized")

    post = await update_post(db, post, data)
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.author), selectinload(Post.tags))
        .where(Post.post_id == post.post_id)
    )
    return result.scalar_one()


@router.post("/{post_id}/close", response_model=PostResponse)
async def close_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("TA", "ADMIN")),
):
    post = await db.get(Post, post_id)
    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")
    post.status = "CLOSED"
    await db.flush()
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.author), selectinload(Post.tags))
        .where(Post.post_id == post.post_id)
    )
    return result.scalar_one()


@router.post("/{post_id}/pin", response_model=PostResponse)
async def pin_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("TA", "ADMIN")),
):
    post = await db.get(Post, post_id)
    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")
    post.is_pinned = not post.is_pinned
    await db.flush()
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.author), selectinload(Post.tags))
        .where(Post.post_id == post.post_id)
    )
    return result.scalar_one()


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN")),
):
    post = await db.get(Post, post_id)
    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)
    await db.flush()
