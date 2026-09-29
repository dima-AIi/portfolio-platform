 Portfolio Platform — Data & API Specification

**Version:** 1.0
**Status:** Approved for development
**Document:** `03_DATA_API.md`

---

# 1. Purpose

Этот документ определяет:

- структуру данных;
- основные сущности;
- связи между сущностями;
- database schema;
- API endpoints;
- форматы request/response;
- правила валидации;
- authentication;
- authorization;
- public portfolio API.

Документ является техническим контрактом между frontend и backend.

Если реализация требует изменения API или структуры данных, изменение сначала должно быть отражено в этом документе.

---

# 2. Core Entities

В MVP используются следующие основные сущности:

```text
User
Profile
Project
Technology
ProjectTechnology
Portfolio
ProjectImage

Связи:

User
 │
 ├── Profile
 │
 ├── Portfolio
 │
 ├── PasswordReset (сброс пароля: код 6 цифр, TTL 15 мин, одноразовый)
 │
 └── Projects
        │
        ├── Technologies
        │
        └── Images
3. User

User представляет зарегистрированного пользователя платформы.

Fields
id
email
username
password_hash
is_active
created_at
updated_at
Rules
id
UUID или integer;
уникальный;
primary key.
email
обязательный;
уникальный;
нормализуется перед сохранением.
username
обязательный;
уникальный;
используется в публичном URL.

Пример:

example.com/dmitriy
password_hash

Никогда не хранить пароль в открытом виде.

4. Profile

Profile содержит публичную информацию пользователя.

Fields
id
user_id
display_name
headline
bio
avatar_url
location
website_url
github_url
linkedin_url
telegram_url
theme
view_count
created_at
updated_at
Example
{
  "display_name": "Dmitriy K.",
  "headline": "Python & Full-Stack Developer",
  "bio": "I build automation tools and web applications.",
  "avatar_url": "/uploads/avatar.jpg",
  "location": "Moscow",
  "github_url": "https://github.com/example"
}
5. Project

Project является основной сущностью продукта.

Именно проекты пользователь показывает потенциальному работодателю или заказчику.

Fields
id
user_id
title
slug
short_description
problem
solution
features
result
role
cover_image_url
github_url
live_url
status
sort_order
view_count
created_at
updated_at
published_at
6. Project Status

Минимально используются два состояния:

DRAFT
PUBLISHED
DRAFT

Проект существует только в dashboard владельца.

PUBLISHED

Проект доступен на публичной странице.

7. Project Content

Каждый проект должен отвечать на четыре основных вопроса:

Что это?
Какую проблему решает?
Что было сделано?
Какой результат?

Структура:

Title
Short Description

Problem
Solution
Features
Result

Role
Tech Stack

GitHub
Live Demo
8. Technology

Technology представляет технологию, использованную в проекте.

Fields
id
name
slug
category

Примеры:

Python
FastAPI
React
TypeScript
PostgreSQL
Docker
Telegram Bot API
9. ProjectTechnology

Many-to-many связь между Project и Technology.

Project
   │
   ├── Python
   ├── FastAPI
   ├── PostgreSQL
   └── Docker
Fields
project_id
technology_id

Composite unique constraint:

(project_id, technology_id)

Одна технология не должна добавляться в один проект несколько раз.

10. ProjectImage

Изображения проекта.

Fields
id
project_id
url
alt_text
sort_order
created_at
Rules
изображение принадлежит конкретному проекту;
пользователь может изменять только изображения своих проектов;
изображения удаляются при удалении проекта либо обрабатываются через cascade policy.
11. Portfolio

Portfolio представляет публичное представление пользователя.

В MVP отдельная сложная сущность Portfolio не обязательна для каждой операции, однако логически она существует как публичный слой пользователя.

Основные данные формируются из:

User
Profile
Projects
Technologies

Публичное портфолио:

/:username
12. Entity Relationships

Основная схема:

USER
 │
 ├─────────────── 1:1 ─────────────── PROFILE
 │
 ├─────────────── 1:N ─────────────── PROJECT
 │                                      │
 │                                      ├── 1:N ── PROJECT_IMAGE
 │                                      │
 │                                      └── N:M ── TECHNOLOGY
 │                                                   │
 │                                      PROJECT_TECHNOLOGY
 │
 └─────────────── PUBLIC PORTFOLIO
13. Database Constraints

Обязательные ограничения:

User.email UNIQUE
User.username UNIQUE

Project.slug + user_id UNIQUE

Technology.slug UNIQUE

ProjectTechnology(project_id, technology_id) UNIQUE

Foreign keys должны использоваться для всех связанных сущностей.

14. Indexes

Минимальные индексы:

users.email
users.username

projects.user_id
projects.slug
projects.status

technologies.slug

project_images.project_id

Особенно важен индекс:

users.username

поскольку username используется при поиске публичного портфолио.

15. Authentication API

Base URL:

/api/v1
POST /auth/register

Регистрация.

Request
{
  "email": "user@example.com",
  "username": "dmitriy",
  "password": "strong-password"
}
Response
{
  "user": {
    "id": "...",
    "email": "user@example.com",
    "username": "dmitriy"
  }
}

После регистрации пользователь может перейти к login.

16. POST /auth/login

Авторизация.

Request
{
  "email": "user@example.com",
  "password": "strong-password"
}
Response
{
  "access_token": "...",
  "token_type": "bearer"
}

Frontend использует token для защищённых API-запросов.

17. GET /auth/me

Возвращает текущего пользователя.

Response
{
  "id": "...",
  "email": "user@example.com",
  "username": "dmitriy"
}

Endpoint требует authentication.

18. Profile API
GET /profile

Возвращает профиль текущего пользователя.

PUT /profile

Обновляет профиль.

Request
{
  "display_name": "Dmitriy",
  "headline": "Python Developer",
  "bio": "I build web applications and automation tools.",
  "location": "Moscow",
  "website_url": "https://example.com",
  "github_url": "https://github.com/example",
  "linkedin_url": "https://linkedin.com/in/example",
  "telegram_url": "https://t.me/example"
}

POST /profile/avatar

Загрузка аватара профиля (multipart/form-data).

Те же правила, что и для изображений проектов:

разрешённые форматы;
ограничение размера;
проверка MIME type;
случайное безопасное имя файла.

Response: обновлённый профиль с avatar_url.
19. Projects API
GET /projects

Возвращает проекты текущего пользователя.

Поддерживается pagination.

Пример:

GET /api/v1/projects?page=1&limit=10
20. POST /projects

Создание проекта.

Request
{
  "title": "Telegram CRM",
  "short_description": "CRM system for Telegram-based businesses.",
  "problem": "Businesses were managing leads manually.",
  "solution": "Built a centralized CRM with Telegram integration.",
  "result": "Automated lead management.",
  "role": "Full-Stack Developer",
  "github_url": "https://github.com/example/project",
  "live_url": "https://example.com"
}

После создания:

status = DRAFT
21. GET /projects/{id}

Возвращает один проект владельца.

22. PUT /projects/{id}

Редактирование проекта.

Пользователь может изменять только собственные проекты.

23. DELETE /projects/{id}

Удаление проекта.

Удаляются или корректно отвязываются:

ProjectTechnology
ProjectImage
24. POST /projects/{id}/publish

Публикация проекта.

После успешного запроса:

status = PUBLISHED
published_at = current_timestamp
25. POST /projects/{id}/unpublish

Скрывает опубликованный проект.

После запроса:

status = DRAFT

25.1 PUT /projects/reorder

Меняет порядок проектов пользователя.

Request
{
  "project_ids": ["...", "...", "..."]
}

Порядок в массиве определяет sort_order (0, 1, 2, ...).

Все id должны принадлежать текущему пользователю, иначе 400.

26. Technologies API
GET /technologies

Возвращает доступные технологии.

Пример:

[
  {
    "id": "...",
    "name": "Python",
    "slug": "python",
    "category": "backend"
  },
  {
    "id": "...",
    "name": "React",
    "slug": "react",
    "category": "frontend"
  }
]
27. Project Technologies
PUT /projects/{id}/technologies

Устанавливает технологии проекта.

Request
{
  "technology_ids": [
    "...",
    "...",
    "..."
  ]
}

Старый список заменяется новым.

28. Images API
POST /projects/{id}/images

Загрузка изображения.

Требования:

только разрешённые image formats;
ограничение размера;
проверка MIME type;
имя файла не должно использоваться напрямую как trusted path.
DELETE /projects/{id}/images/{image_id}

Удаление изображения.

Проверяется ownership проекта.

29. GitHub API

GitHub используется только для чтения публичных данных и только
по инициативе владельца аккаунта.

GET /github/repos?username=<handle>

Требует authentication. Backend обращается к публичному API GitHub
**без токена и без OAuth**. Форки исключены, ничего не сохраняется.

Response:

{
  "repos": [
    {
      "name": "telegram-crm",
      "description": "CRM for Telegram businesses",
      "url": "https://github.com/example/telegram-crm",
      "language": "Python",
      "stars": 4,
      "forks": 1,
      "topics": ["crm", "telegram"],
      "homepage": "",
      "archived": false,
      "updated_at": "2026-09-01T10:00:00Z"
    }
  ],
  "count": 1
}

Ошибки: 404 GITHUB_USER_NOT_FOUND, 429 GITHUB_RATE_LIMIT,
502 GITHUB_UNAVAILABLE / GITHUB_ERROR.

30. Импорт репозитория в проект

Отдельного эндпоинта импорта нет: выбранный репозиторий превращается
в проект обычным POST /projects, который создаёт DRAFT-черновик.
Пользователь редактирует его вручную и публикует сам.

Backend:

GitHub
 ↓
Repository metadata (GET /github/repos)
 ↓
Frontend заполняет форму
 ↓
POST /projects
 ↓
DRAFT
 ↓
User edits
 ↓
Publish

31. AI API

AI-функции являются помощником, а не источником истины.

POST /ai/project-description

Создаёт предложение по описанию проекта.

Request
{
  "title": "Telegram CRM",
  "description": "CRM bot for managing leads",
  "technologies": [
    "Python",
    "FastAPI",
    "PostgreSQL"
  ]
}
Response
{
  "short_description": "...",
  "problem": "...",
  "solution": "...",
  "result": "..."
}

Результат не сохраняется автоматически.

Пользователь сначала подтверждает его.

32. AI Confirmation Rule

AI-generated content имеет состояние:

GENERATED

Пользователь должен самостоятельно подтвердить его перед публикацией.

Flow:

User data
   ↓
AI
   ↓
Generated draft
   ↓
User review
   ↓
Accept
   ↓
Project
   ↓
Publish

AI никогда не должен автоматически публиковать контент.

33. Public Portfolio API

Публичные endpoints не требуют authentication.

GET /public/{username}

Возвращает публичный профиль.

Response
{
  "username": "dmitriy",
  "profile": {
    "display_name": "Dmitriy",
    "headline": "Python Developer",
    "bio": "..."
  },
  "projects": []
}

В ответ попадают только:

PUBLISHED

проекты.

34. GET /public/{username}/projects/{slug}

Возвращает один публичный проект.

Проект должен:

status = PUBLISHED

и принадлежать указанному пользователю.

35. Public Data Restrictions

Публичный API никогда не должен возвращать:

password_hash;
email, если пользователь не решил его показывать;
authentication tokens;
private projects;
private GitHub data;
internal database IDs без необходимости;
системные данные.
36. Pagination

Для потенциально больших списков используется:

page
limit

Например:

GET /projects?page=1&limit=20

Response:

{
  "items": [],
  "page": 1,
  "limit": 20,
  "total": 42
}
37. Validation

Backend обязан валидировать все входные данные.

Проверяются:

email;
username;
password;
URLs;
project title;
project text length;
technology IDs;
image type;
image size.

Frontend validation используется для UX, но не заменяет backend validation.

38. Username Rules

Username:

уникальный;
lowercase;
без пробелов;
содержит только разрешённые символы (a-z, 0-9, дефис, подчёркивание; 3–30 символов);
не совпадает с зарезервированными словами (login, register, dashboard, api, admin, settings, public, uploads, static), чтобы не конфликтовать с системными routes.

Пример допустимого:

dmitriy
dmitriy_dev
dev-dmitriy

Примеры недопустимого:

Dmitriy Dev
user@example.com
39. Slug Rules

Project slug создаётся из названия.

Пример:

Telegram CRM

↓

telegram-crm

Если slug уже существует у пользователя:

telegram-crm-2

Slug используется для публичного URL.

40. API Response Principles

API должен возвращать JSON.

Одиночный ресурс возвращается напрямую как JSON object:

{
  "id": "...",
  "title": "..."
}

Collection возвращается с pagination envelope:

{
  "items": [],
  "page": 1,
  "limit": 20,
  "total": 42
}

Ошибки имеют единый формат:

{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project not found."
  }
}
41. Error Codes

Минимальные application errors:

INVALID_CREDENTIALS
EMAIL_ALREADY_EXISTS
USERNAME_ALREADY_EXISTS
PROJECT_NOT_FOUND
PROJECT_ACCESS_DENIED
PROJECT_ALREADY_PUBLISHED
PROJECT_NOT_PUBLISHED
INVALID_IMAGE
FILE_TOO_LARGE
GITHUB_IMPORT_FAILED
AI_GENERATION_FAILED
42. Ownership Rules

Для любого защищённого Project endpoint:

authenticated_user.id
        ==
project.user_id

Если условие не выполняется:

403 Forbidden

или 404 Not Found, если выбран подход, скрывающий существование ресурса.

Frontend не определяет ownership.

43. API Security Rules

Обязательные правила:

Все protected endpoints требуют authentication.
Ownership проверяется backend.
Password никогда не возвращается API.
API keys никогда не возвращаются frontend.
AI requests проходят через backend.
GitHub integration проходит через backend.
Uploads проходят validation.
Пользовательские URL проходят validation.
Sensitive information не записывается в logs.
44. MVP API Summary

Минимальный API:

AUTH
POST   /auth/register
POST   /auth/login
GET    /auth/me
PUT    /auth/password
PUT    /auth/email
DELETE /auth/account
POST   /auth/reset-request
POST   /auth/reset-confirm

PROFILE
GET    /profile
PUT    /profile
POST   /profile/avatar

PROJECTS
GET    /projects
POST   /projects
GET    /projects/{id}
PUT    /projects/{id}
DELETE /projects/{id}
PUT    /projects/reorder

PUBLISH
POST   /projects/{id}/publish
POST   /projects/{id}/unpublish

TECHNOLOGIES
GET    /technologies
PUT    /projects/{id}/technologies

IMAGES
POST   /projects/{id}/images
DELETE /projects/{id}/images/{image_id}

PUBLIC
GET    /public/{username}
GET    /public/{username}/projects/{slug}

OWNER (требуют authentication, только свои данные)
GET    /analytics?days=30
GET    /export
GET    /github/repos?username=<handle>
GET    /public/sitemap.xml

GITHUB (публичный API, без токена и OAuth — только чтение):
GET    /github/repos?username=<handle>

AI endpoint (POST-MVP, не реализован):
POST   /ai/project-description
45. API Priority
P0 — обязательно
Authentication (cookie session + Bearer fallback)
Profile
Projects CRUD
Project publishing
Public portfolio
Technologies
Images
P1 — реализовано
Analytics (page_views, бакеты источников)
Data export
GitHub import (публичный API, без токена)
Themes
SEO: sitemap.xml, robots.txt, JSON-LD
Cookie session вместо токена в localStorage
P2 — позже
Email verification
Custom domains
Portfolio templates
Advanced AI
46. Data Flow — Create Project
User
 ↓
Project Form
 ↓
POST /projects
 ↓
FastAPI
 ↓
Validation
 ↓
Authorization
 ↓
Project Service
 ↓
PostgreSQL
 ↓
Response
 ↓
Dashboard
47. Data Flow — Publish Project
User
 ↓
Publish
 ↓
POST /projects/{id}/publish
 ↓
Authentication
 ↓
Ownership Check
 ↓
Validation
 ↓
status = PUBLISHED
 ↓
published_at
 ↓
PostgreSQL
 ↓
Public Portfolio
48. Data Flow — GitHub Repos
User
 ↓
Dashboard → «Импорт из GitHub»
 ↓
GET /github/repos?username=<handle>
 ↓
GitHub Service
 ↓
GitHub public API (no token)
 ↓
Normalize Data (forks dropped)
 ↓
Owner picks repositories
 ↓
POST /projects → DRAFT
 ↓
User edits
 ↓
Publish
49. Data Flow — AI
User
 ↓
"Improve with AI"
 ↓
POST /ai/project-description
 ↓
Backend validation
 ↓
AI Service
 ↓
AI Provider
 ↓
Structured JSON
 ↓
Validation
 ↓
Frontend preview
 ↓
User confirms
 ↓
Project updated
50. Final Data/API Contract

На этапе MVP система должна придерживаться следующего принципа:

Database хранит источник истины. Backend контролирует бизнес-логику и безопасность. Frontend отвечает за интерфейс. AI и GitHub являются внешними помощниками и никогда не получают прямой доступ к базе данных.

Основной flow продукта:

REGISTER
   ↓
CREATE PROFILE
   ↓
CREATE PROJECT
   ↓
ADD CASE STUDY
   ↓
ADD TECHNOLOGIES
   ↓
OPTIONAL: GITHUB IMPORT
   ↓
OPTIONAL: AI ASSIST
   ↓
USER REVIEW
   ↓
PUBLISH
   ↓
PUBLIC PORTFOLIO