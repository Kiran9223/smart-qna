import uuid
from datetime import datetime, timezone
from sqlalchemy import Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Comment(Base):
    __tablename__ = "comments"

    comment_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    post_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("posts.post_id", ondelete="CASCADE"))
    answer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("answers.answer_id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    author = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    answer = relationship("Answer", back_populates="comments")

    __table_args__ = (
        Index("idx_comments_post_id", "post_id"),
        Index("idx_comments_answer_id", "answer_id"),
    )
