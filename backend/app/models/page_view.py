import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, utcnow


class PageView(Base):
    """One public page view, recorded for the owner's analytics.

    Kept separate from the denormalised Project.view_count / Profile.view_count
    counters: those give a fast total, while this table holds the detail
    needed to answer "where did these visits come from and which case study
    actually gets opened".
    """

    __tablename__ = "page_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # NULL for the portfolio page, set for a case study page.
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # Coarse bucket such as "telegram", "github", "direct", "google".
    referrer: Mapped[str | None] = mapped_column(String(64), index=True)
    path: Mapped[str] = mapped_column(String(200))
    user_agent_family: Mapped[str | None] = mapped_column(String(32))
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
