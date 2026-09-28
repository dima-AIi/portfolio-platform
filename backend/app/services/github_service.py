"""Reads a public GitHub profile so its repos can seed real projects.

Uses the unauthenticated public API on purpose: no token, no account linking,
no scope creep. Nothing is persisted — the owner picks what to import, and only
the chosen repos become projects.
"""

import httpx
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.errors import AppError

GITHUB_API = "https://api.github.com"
# httpx reads a bare number as a port, so the timeout needs its unit.
TIMEOUT_SECONDS = httpx.Timeout(10.0)


class GitHubImportService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    async def list_repos(self, username: str) -> list[dict]:
        handle = username.strip().lstrip("@").strip("/")
        if not handle or "/" in handle or len(handle) > 39:
            raise AppError(
                "INVALID_GITHUB_USER",
                "Укажите имя пользователя GitHub латиницей, без ссылки на профиль.",
                400,
            )

        try:
            async with httpx.AsyncClient(
                timeout=TIMEOUT_SECONDS,
                # Some Windows setups export NO_PROXY with bracketed IPv6
                # entries ("::1" as "[::1]"), which httpx cannot parse and
                # then fails on before any request is made. GitHub is
                # reached directly, so env proxies are not consulted.
                trust_env=False,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "Portfolio-Platform",
                },
            ) as client:
                resp = await client.get(
                    f"{GITHUB_API}/users/{handle}/repos", params={"per_page": 100}
                )
        except httpx.HTTPError as exc:
            raise AppError(
                "GITHUB_UNAVAILABLE",
                "Не удалось связаться с GitHub. Попробуйте позже.",
                502,
            ) from exc

        if resp.status_code == 404:
            raise AppError(
                "GITHUB_USER_NOT_FOUND", "Пользователь с таким именем не найден.", 404
            )
        if resp.status_code in (403, 429):
            raise AppError(
                "GITHUB_RATE_LIMIT",
                "GitHub временно ограничил число запросов. Попробуйте позже.",
                429,
            )
        if resp.status_code != 200:
            raise AppError("GITHUB_ERROR", "GitHub вернул ошибку.", 502)

        # Forks rarely represent original work, so they are left out of the
        # import list instead of being offered as lower-ranked noise.
        return [
            {
                "name": r["name"],
                "description": r.get("description") or "",
                "url": r.get("html_url", ""),
                "language": r.get("language"),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "updated_at": r.get("updated_at"),
                "topics": (r.get("topics") or [])[:6],
                "homepage": r.get("homepage") or "",
                "archived": r.get("archived", False),
            }
            for r in resp.json()
            if not r.get("fork")
        ]
