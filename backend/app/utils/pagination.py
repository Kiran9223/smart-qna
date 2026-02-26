from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int


async def paginate(db: AsyncSession, query, page: int = 1, size: int = 20):
    size = min(size, 100)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    items = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }
