"""Owner-facing data services: analytics, full export, GitHub import."""

import uuid

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db, utcnow
from app.repositories.page_view_repository import PageViewRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.utils.errors import AppError

EXPORT_FORMAT_VERSION = 1


class AnalyticsService:
    """Read-only summary of who visits the portfolio and what they open."""

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.views = PageViewRepository(db)

    def summary(self, user_id: uuid.UUID, days: int = 30) -> dict:
        from app.utils.analytics import DIRECT

        daily = self.views.daily(user_id, days=14)
        sources = self.views.by_referrer(user_id, days=days)
        by_source = {s["source"]: s["views"] for s in sources}
        return {
            "window_days": days,
            "total_views": self.views.total_views(user_id),
            "window_views": sum(by_source.values()),
            "daily": daily,
            "sources": sources[:6],
            "top_projects": self.views.top_projects(user_id, days=days)[:5],
            "direct_views": by_source.get(DIRECT, 0),
            "recent": self.views.recent(user_id, limit=15),
        }


class ExportService:
    """Full data export.

    Read.cv and bento.me both shut down and took years of user work with
    them. A one-file JSON dump is the cheapest way to make that impossible
    here: the content outlives the account.
    """

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.projects = ProjectRepository(db)
        self.profiles = ProfileRepository(db)
        self.users = UserRepository(db)

    def build(self, user_id: uuid.UUID) -> dict:
        user = self.users.get_by_id(user_id)
        if not user:
            raise AppError("USER_NOT_FOUND", "Пользователь не найден.", 404)
        profile = self.profiles.get_by_user_id(user_id)
        return {
            "format": "portfolio-platform-export",
            "format_version": EXPORT_FORMAT_VERSION,
            "exported_at": utcnow().isoformat(),
            "account": {"email": user.email, "username": user.username},
            "profile": self._profile_to_dict(profile),
            "projects": [
                {
                    "title": p.title,
                    "slug": p.slug,
                    "short_description": p.short_description,
                    "problem": p.problem,
                    "solution": p.solution,
                    "features": p.features,
                    "result": p.result,
                    "role": p.role,
                    "cover_image_url": p.cover_image_url,
                    "github_url": p.github_url,
                    "live_url": p.live_url,
                    "status": p.status,
                    "sort_order": p.sort_order,
                    "technologies": [t.name for t in p.technologies],
                    "images": [{"url": i.url, "alt_text": i.alt_text} for i in p.images],
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "published_at": p.published_at.isoformat() if p.published_at else None,
                }
                for p in self.projects.list_by_user(user_id)
            ],
        }

    @staticmethod
    def _profile_to_dict(profile) -> dict | None:
        if not profile:
            return None
        return {
            "display_name": profile.display_name,
            "headline": profile.headline,
            "bio": profile.bio,
            "location": profile.location,
            "website_url": profile.website_url,
            "github_url": profile.github_url,
            "linkedin_url": profile.linkedin_url,
            "telegram_url": profile.telegram_url,
            "avatar_url": profile.avatar_url,
            "theme": profile.theme,
        }
