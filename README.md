# Portfolio Platform

Сервис для создания профессионального портфолио: пользователь собирает свои проекты в виде кейсов
(**Problem → Solution → Result → Tech Stack**) и получает публичную страницу портфолио по одной ссылке.

## Tech stack

| Layer    | Technologies |
|----------|--------------|
| Frontend | React 18, TypeScript, Vite, React Router |
| Backend  | Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT |
| Database | PostgreSQL (production) / SQLite (local dev) |
| Infra    | Docker, Docker Compose |

## Quick start

### Вариант 1: Docker (рекомендуется)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/v1
- API docs: http://localhost:8000/docs

### Вариант 2: Локально (без Docker)

Требуется Python 3.12+ и Node 18+.

```bash
# 1. Environment
cp .env.example .env

# 2. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Frontend (в новом терминале)
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173 (проксирует `/api` и `/uploads` на backend)
- Backend: http://localhost:8000

## Структура проекта

```text
portfolio-platform/
├── backend/            FastAPI application
│   ├── app/
│   │   ├── api/        Routers (HTTP layer)
│   │   ├── core/       Config, security, database
│   │   ├── models/     SQLAlchemy models
│   │   ├── schemas/    Pydantic schemas
│   │   ├── services/   Business logic
│   │   └── repositories/  DB queries
│   ├── alembic/        Migrations
│   └── tests/          pytest
├── frontend/           React + TypeScript (Vite)
│   └── src/
│       ├── app/        Router, providers
│       ├── pages/      Page components
│       ├── components/ UI components
│       ├── services/   API client
│       └── types/      Shared TS types
├── docs/               Project documentation
├── docker-compose.yml
└── .env.example
```

## API

Все endpoints доступны под префиксом `/api/v1`. Swagger: http://localhost:8000/docs

```text
AUTH         POST /auth/register, POST /auth/login, POST /auth/logout, GET /auth/me
SESSION      httpOnly cookie `portfolio_session` (SameSite=Lax) — the JWT is
             never returned in the response body and never stored in JS.
             `Authorization: Bearer <jwt>` also works for API clients.
PROFILE      GET/PUT /profile, POST /profile/avatar
PROJECTS     GET/POST /projects, GET/PUT/DELETE /projects/{id}, PUT /projects/reorder
PUBLISH      POST /projects/{id}/publish, POST /projects/{id}/unpublish
TECH         GET /technologies, PUT /projects/{id}/technologies
IMAGES       POST /projects/{id}/images, DELETE /projects/{id}/images/{image_id}
PUBLIC       GET /public/{username}, GET /public/{username}/projects/{slug}
SITEMAP      GET /public/sitemap.xml
```

`GET /public/{username}` accepts optional `?page=&limit=` (max 50). `skills`
always covers the whole portfolio, not just the current page.

### Session, CSRF and rate limiting

The session cookie (`SameSite=Lax`, `HttpOnly`, `Secure` in production) is
the CSRF defence, and for the current endpoint set it is sufficient on its
own:

* every state-changing request is `POST`, `PUT` or `DELETE`, and browsers do
  not attach `Lax` cookies to cross-site requests of those methods;
* all of them require a JSON body, so a cross-origin attempt triggers a CORS
  preflight that the allow-list rejects;
* no endpoint performs a state change on `GET`.

A separate CSRF token would only be required if a `GET` ever mutated state
or if `SameSite=None` were needed for a cross-site embedding. Neither
applies today, so no token is issued.

Rate limits on `/auth/*` are an in-memory sliding window keyed by client IP
plus path. Behind a proxy the right-most `X-Forwarded-For` entry is used,
because that is the address the trusted proxy appended and therefore the one
a client cannot forge.

## Showcase portfolio

The landing page links to a filled demo account so a visitor can see a real page
before registering. The ELORA case study documents an actual deployed project
(an online booking service for a beauty studio) in the
Problem → Solution → Result → Stack shape.

```bash
# Backend must be running on :8000
cd backend
python scripts/seed_showcase.py
```

This creates `@demo` with the profile, the published project, its technologies
and screenshots pulled from the live site, then publishes it:

| | |
|---|---|
| Public page | http://localhost:5173/demo |
| Login | `demo@portfolio-platform.dev` / `showcase-2026` |

The script is idempotent — re-running it updates the existing project instead of
creating duplicates, and it skips image upload once the project has images.

## Seeding a real portfolio

To stand up a personal account with the same ELORA case study, use
`seed_owner_portfolio.py`. Credentials come from the environment so a password
never lands in the repository:

```bash
cd backend
export SEED_EMAIL=you@example.com
export SEED_USERNAME=yourhandle
export SEED_PASSWORD='...'
export SEED_BASE=https://your-backend.example.com   # default localhost:8000
python scripts/seed_owner_portfolio.py
```

It creates the account if needed (or logs in), fills the profile, writes the
ELORA case study with its technologies and screenshots, and publishes it.
The password is never echoed and never committed.

## Removing accounts

The API intentionally has no "delete any account" endpoint. To clear demo
accounts out of a database, use the operator script. It is **dry-run by
default**:

```bash
export DATABASE_URL=postgresql://...
python scripts/remove_accounts.py demo demo-start        # shows what it would delete
python scripts/remove_accounts.py --confirm demo demo-start
KEEP_USERNAME=yourhandle python scripts/remove_accounts.py --confirm demo
```

Uploaded image files are not touched — they live on the app server's disk, not
in the database.

## Testing

```bash
# Backend — 123 tests (lint first, since CI runs it too)
cd backend
ruff check .
pytest

# Frontend — 26 tests
cd frontend
npm run lint
npm run typecheck
npm test
```

Both suites run in CI on every push and pull request (`.github/workflows/ci.yml`).

## Deployment (free tier)

The project is configured for a free public deployment:

- **Vercel** — frontend (`frontend/vercel.json` proxies `/api` and `/uploads` to the backend)
- **Render** — backend (Dockerfile, pre-deploy command: `alembic upgrade head`)
- **Neon** — managed PostgreSQL (free tier)

Environment variables for Render:

```text
DATABASE_URL   = postgresql+psycopg2://... (Neon connection string)
JWT_SECRET     = <random 64-hex string>
CORS_ORIGINS   = https://<your-app>.vercel.app
PUBLIC_URL     = https://<your-app>.vercel.app   # used by sitemap.xml
```

### Email for password reset codes

Set SMTP credentials to send real 6-digit reset codes
(otherwise, in development mode the code is shown in the UI):

```text
SMTP_HOST      = smtp.gmail.com        # or smtp.yandex.ru, smtp.mail.ru, smtp.mailtrap.io
SMTP_PORT      = 587
SMTP_USER      = you@gmail.com         # Gmail requires an App Password
SMTP_PASSWORD  = <app password>
SMTP_FROM      = you@gmail.com
SMTP_TLS       = true
```

After deploying Render, replace `REPLACE_WITH_RENDER_URL.onrender.com`
in `frontend/vercel.json` with your real Render URL, then deploy the
`frontend/` directory on Vercel.

## Documentation

Полная документация продукта и архитектуры — в `docs/`.
