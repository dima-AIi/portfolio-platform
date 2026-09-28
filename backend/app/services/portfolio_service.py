from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.portfolio import PublicPortfolioResponse, PublicProjectResponse
from app.schemas.profile import ProfileResponse
from app.schemas.project import ProjectResponse
from app.utils.errors import AppError
from app.utils.sitemap import render_sitemap


class PortfolioService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.repo = ProjectRepository(db)
        self.users = UserRepository(db)

    def build_sitemap(self) -> str:
        """Render sitemap.xml for every public portfolio and project page.

        Crawlers only accept absolute URLs, so the PUBLIC_URL setting decides
        which origin the entries point at. Draft projects and inactive
        accounts are never listed.
        """
        base = settings.PUBLIC_URL.rstrip("/")
        urls: list[tuple[str, str | None]] = [(f"{base}/", None)]
        for username in self.repo.list_public_usernames():
            urls.append((f"{base}/{username}", None))
            user = self.users.get_by_username(username)
            if not user:
                continue
            for slug in self.repo.list_published_slugs(user.id):
                urls.append((f"{base}/{username}/projects/{slug}", None))
        return render_sitemap(urls)

    def get_portfolio(
        self,
        username: str,
        page: int | None = None,
        limit: int | None = None,
    ) -> PublicPortfolioResponse:
        user = self.users.get_by_username(username.lower())
        if not user:
            raise AppError("PORTFOLIO_NOT_FOUND", "Портфолио не найдено.", 404)
        profile = user.profile
        if not profile:
            raise AppError("PORTFOLIO_NOT_FOUND", "Портфолио не найдено.", 404)
        profile.view_count += 1
        self.db.commit()

        if page is not None and limit is not None:
            offset = (page - 1) * limit
            projects = self.repo.list_published_by_user(user.id, limit=limit, offset=offset)
            total = self.repo.count_published_by_user(user.id)
            # Skills describe the whole portfolio, not just the visible page —
            # otherwise the tech section would change as the user clicks "more".
            skill_source = self.repo.list_published_by_user(user.id)
        else:
            projects = self.repo.list_published_by_user(user.id)
            skill_source = projects
            total = len(projects)

        skills = sorted({t.name for p in skill_source for t in p.technologies})
        return PublicPortfolioResponse(
            username=user.username,
            profile=ProfileResponse.model_validate(profile),
            projects=[ProjectResponse.model_validate(p) for p in projects],
            skills=skills,
            total=total,
            page=page,
            limit=limit,
        )

    def get_public_project(self, username: str, slug: str) -> PublicProjectResponse:
        user = self.users.get_by_username(username.lower())
        if not user:
            raise AppError("PROJECT_NOT_FOUND", "Проект не найден.", 404)
        project = next(
            (p for p in self.repo.list_published_by_user(user.id) if p.slug == slug), None
        )
        if not project:
            raise AppError("PROJECT_NOT_FOUND", "Проект не найден.", 404)
        project.view_count += 1
        self.db.commit()
        return PublicProjectResponse(
            username=user.username,
            theme=user.profile.theme if user.profile else "classic",
            project=ProjectResponse.model_validate(project),
        )

