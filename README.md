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
AUTH         POST /auth/register, POST /auth/login, GET /auth/me
PROFILE      GET/PUT /profile, POST /profile/avatar
PROJECTS     GET/POST /projects, GET/PUT/DELETE /projects/{id}, PUT /projects/reorder
PUBLISH      POST /projects/{id}/publish, POST /projects/{id}/unpublish
TECH         GET /technologies, PUT /projects/{id}/technologies
IMAGES       POST /projects/{id}/images, DELETE /projects/{id}/images/{image_id}
PUBLIC       GET /public/{username}, GET /public/{username}/projects/{slug}
```

## Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

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
