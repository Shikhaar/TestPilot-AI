"""TestPilot AI — Review Comment ORM Model."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin


class ReviewComment(Base, UUIDMixin, TimestampMixin):
    """Represents an AI-generated GitHub PR review comment.

    Attributes:
        pull_request_id: FK to the reviewed pull request.
        github_comment_id: GitHub's ID for the posted comment.
        github_review_id: GitHub's review ID.
        body: Full review comment body (Markdown).
        risk_level: Overall risk: 'low' | 'medium' | 'high' | 'critical'.
        risk_score: Numeric risk (0.0 - 10.0).
        summary: Short executive summary.
        action_items: JSON list of suggested action items.
        is_posted: Whether this review has been posted to GitHub.
        posted_at: Timestamp when posted.
        model_used: LLM model used to generate the review.
        prompt_tokens: Tokens in the generation prompt.
        completion_tokens: Tokens in the completion.
    """

    __tablename__ = "review_comments"

    pull_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    github_comment_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    github_review_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="low", nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_items: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    is_posted: Mapped[bool] = mapped_column(String(5), default=False, nullable=False)
    posted_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # AI metadata
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(String(10), nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(String(10), nullable=True)

    # Relationships
    pull_request: Mapped[PullRequest] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "PullRequest",
        back_populates="review_comments",
    )

    def __repr__(self) -> str:
        return f"<ReviewComment id={self.id} risk={self.risk_level} posted={self.is_posted}>"
