import uuid
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import utcnow
from app.models import PageView, Project


class PageViewRepository:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        user_id: uuid.UUID,
        path: str,
        project_id: uuid.UUID | None = None,
        referrer: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        from app.utils.analytics import browser_family, classify_referrer

        # The raw Referer header is never stored: it can embed a private path
        # or a search query. Only the coarse bucket survives.
        self.db.add(
            PageView(
                user_id=user_id,
                project_id=project_id,
                referrer=classify_referrer(referrer),
                path=path[:200],
                user_agent_family=browser_family(user_agent),
            )
        )
        self.db.commit()

    def total_views(self, user_id: uuid.UUID) -> int:
        return (
            self.db.scalar(
                select(func.count()).select_from(PageView).where(PageView.user_id == user_id)
            )
            or 0
        )

    def by_referrer(self, user_id: uuid.UUID, days: int = 30) -> list[dict]:
        since = utcnow() - timedelta(days=days)
        from app.utils.analytics import DIRECT

        rows = self.db.execute(
            select(PageView.referrer, func.count())
            .where(PageView.user_id == user_id, PageView.viewed_at >= since)
            .group_by(PageView.referrer)
            .order_by(func.count().desc())
        ).all()
        return [
            {"source": r or DIRECT, "views": count} for r, count in rows
        ]

    def top_projects(self, user_id: uuid.UUID, days: int = 30) -> list[dict]:
        """Case studies ordered by how often they were actually opened."""
        since = utcnow() - timedelta(days=days)
        rows = self.db.execute(
            select(Project.id, Project.title, Project.slug, func.count(PageView.id))
            .join(PageView, PageView.project_id == Project.id)
            .where(Project.user_id == user_id, PageView.viewed_at >= since)
            .group_by(Project.id, Project.title, Project.slug)
            .order_by(func.count(PageView.id).desc())
        ).all()
        return [
            {"id": str(pid), "title": title, "slug": slug, "views": views}
            for pid, title, slug, views in rows
        ]

    def daily(self, user_id: uuid.UUID, days: int = 14) -> list[dict]:
        """Per-day totals for a sparkline, oldest first, with empty days filled."""
        since = utcnow() - timedelta(days=days - 1)
        rows = self.db.execute(
            select(PageView.viewed_at).where(
                PageView.user_id == user_id, PageView.viewed_at >= since
            )
        ).scalars().all()
        counts: dict[str, int] = {}
        for seen in rows:
            key = seen.date().isoformat()
            counts[key] = counts.get(key, 0) + 1
        today = utcnow().date()
        out = []
        for offset in range(days - 1, -1, -1):
            day = (today - timedelta(days=offset)).isoformat()
            out.append({"date": day, "views": counts.get(day, 0)})
        return out

    def recent(self, user_id: uuid.UUID, limit: int = 20) -> list[dict]:
        rows = self.db.execute(
            select(PageView, Project.title, Project.slug)
            .outerjoin(Project, Project.id == PageView.project_id)
            .where(PageView.user_id == user_id)
            .order_by(PageView.viewed_at.desc())
            .limit(limit)
        ).all()
        from app.utils.analytics import DIRECT

        return [
            {
                "date": view.viewed_at.isoformat(),
                "source": view.referrer or DIRECT,
                "device": view.user_agent_family or "Неизвестно",
                "path": view.path,
                "project_title": title,
                "project_slug": slug,
            }
            for view, title, slug in rows
        ]

    def delete_for_user(self, user_id: uuid.UUID) -> None:
        """Drop a user's analytics rows.

        page_views has no ORM relationship to User, so the ORM cascade does not
        cover it. The `ondelete="CASCADE"` on the column only fires where the
        database enforces foreign keys — SQLite does not unless explicitly
        enabled — which silently left traffic rows behind after an account
        deletion. Deleting them explicitly works on every backend.
        """
        self.db.query(PageView).filter(PageView.user_id == user_id).delete(
            synchronize_session=False
        )
        self.db.commit()
