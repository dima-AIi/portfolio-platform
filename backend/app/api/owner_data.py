"""Owner-only endpoints: analytics, data export and GitHub import."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.api.auth import get_current_user
from app.models import User
from app.services.github_service import GitHubImportService
from app.services.owner_data_service import AnalyticsService, ExportService

router = APIRouter(tags=["owner"])


@router.get("/analytics")
def get_analytics(
    days: int = Query(default=30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(),
):
    """Where the visits come from and which case studies get opened."""
    return service.summary(current_user.id, days=days)


@router.get("/export")
def export_data(
    current_user: User = Depends(get_current_user),
    service: ExportService = Depends(),
):
    """Everything the account holds, as a downloadable JSON file.

    The account can be deleted, but this file keeps the work. Read.cv and
    bento.me showed what happens to hosted portfolios when a platform folds.
    """
    payload = service.build(current_user.id)
    return JSONResponse(
        content=payload,
        headers={
            # Forces a save dialog instead of rendering JSON in the tab.
            "Content-Disposition": f'attachment; filename="portfolio-{current_user.username}.json"'
        },
    )


@router.get("/github/repos")
async def github_repos(
    username: str = Query(..., min_length=1, max_length=100),
    current_user: User = Depends(get_current_user),
    service: GitHubImportService = Depends(),
):
    """Public repositories for a GitHub handle, ready to become projects."""
    repos = await service.list_repos(username)
    return {"repos": repos, "count": len(repos)}
