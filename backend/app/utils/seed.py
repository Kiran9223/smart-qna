"""Run with: python -m app.utils.seed"""
import asyncio
from app.database import async_session
from app.models.tag import Tag

DEFAULT_TAGS = [
    "setup", "spring-boot", "kafka", "exam", "general",
    "debugging", "database", "docker", "python", "react",
]


async def seed():
    async with async_session() as session:
        for tag_name in DEFAULT_TAGS:
            tag = Tag(name=tag_name)
            session.add(tag)
        try:
            await session.commit()
            print(f"Seeded {len(DEFAULT_TAGS)} tags.")
        except Exception:
            await session.rollback()
            print("Tags already exist, skipping seed.")


if __name__ == "__main__":
    asyncio.run(seed())
