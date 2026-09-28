from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/public", tags=["public"])


# Declared before "/{username}" on purpose: routes match in declaration order,
# so a later dynamic path would otherwise swallow the literal "sitemap.xml".
@router.get("/sitemap.xml", include_in_schema=False)
def sitemap(service: PortfolioService = Depends()) -> PlainTextResponse:
    return PlainTextResponse(
        service.build_sitemap(),
        media_type="application/xml; charset=utf-8",
    )


@router.get("/{username}")
def get_portfolio(
    username: str,
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=50),
    service: PortfolioService = Depends(),
):
    return service.get_portfolio(username, page, limit)


@router.get("/{username}/projects/{slug}")
def get_public_project(username: str, slug: str, service: PortfolioService = Depends()):
    return service.get_public_project(username, slug)
