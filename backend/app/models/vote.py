import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Vote(Base):
    __tablename__ = "votes"

    vote_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    post_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("posts.post_id", ondelete="CASCADE"))
    answer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("answers.answer_id", ondelete="CASCADE"))
    vote_type: Mapped[str] = mapped_column(String(4), nullable=False)  # UP, DOWN
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="votes")
    post = relationship("Post", back_populates="votes")
    answer = relationship("Answer", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_vote_post_user"),
        UniqueConstraint("answer_id", "user_id", name="uq_vote_answer_user"),
        CheckConstraint(
            "(post_id IS NOT NULL AND answer_id IS NULL) OR (post_id IS NULL AND answer_id IS NOT NULL)",
            name="chk_vote_target",
        ),
        Index("idx_votes_user_id", "user_id"),
    )
