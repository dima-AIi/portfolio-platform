# Portfolio Platform — Development Rules

**Version:** 1.0
**Status:** Approved
**Document:** `04_DEVELOPMENT_RULES.md`

---

# 1. Purpose

Этот документ определяет правила разработки Portfolio Platform.

Он используется как постоянный технический регламент проекта.

Основная задача документа:

* определить порядок разработки;
* зафиксировать требования к качеству кода;
* определить правила frontend и backend;
* определить правила работы с базой данных;
* определить правила Git;
* определить правила тестирования;
* определить правила безопасности;
* определить правила использования AI;
* определить критерии готовности функциональности;
* предотвратить хаотичные изменения архитектуры.

---

# 2. Main Development Principle

Главный принцип:

> **Сначала рабочая архитектура и логика, затем визуальная полировка.**

Проект не должен строиться как набор красивых страниц без полноценного backend.

Каждая основная функция должна иметь понятный путь:

```text
User
 ↓
Frontend
 ↓
API
 ↓
Business Logic
 ↓
Database
 ↓
Response
 ↓
Frontend
```

---

# 3. MVP First

Первоначальная версия должна быть минимальной, но полностью рабочей.

MVP должен позволять пользователю:

```text
1. Зарегистрироваться
2. Войти
3. Создать профиль
4. Создать проект
5. Добавить описание проекта
6. Добавить технологии
7. Редактировать проект
8. Удалить проект
9. Опубликовать проект
10. Получить публичную страницу портфолио
```

Только после этого добавляются:

* GitHub import;
* AI;
* analytics;
* дополнительные темы;
* custom domains;
* расширенные настройки.

---

# 4. Development Order

Разработка выполняется в следующем порядке:

```text
1. Project setup
2. Backend foundation
3. Database
4. Authentication
5. Profile
6. Projects CRUD
7. Technologies
8. Publishing
9. Public portfolio
10. Frontend dashboard
11. Frontend public portfolio
12. Images
13. GitHub integration
14. AI assistant
15. Testing
16. Security review
17. Deployment
18. Visual polish
```

Не следует начинать с AI.

Не следует начинать с сложной анимации.

Не следует начинать с дополнительных функций.

---

# 5. Repository Structure

Предполагаемая структура:

```text
portfolio-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   └── utils/
│   │
│   ├── public/
│   ├── package.json
│   └── Dockerfile
│
├── docs/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

Структура может немного изменяться при реализации, если это улучшает архитектуру.

Но без необходимости структура не должна перестраиваться.

---

# 6. Backend Rules

Backend строится на:

```text
Python
FastAPI
PostgreSQL
SQLAlchemy
Alembic
Pydantic
```

Основные уровни:

```text
API
 ↓
Service
 ↓
Repository
 ↓
Database
```

---

# 7. API Layer

API отвечает за:

* HTTP;
* authentication dependency;
* validation input;
* response schemas;
* status codes.

API layer не должен содержать сложную бизнес-логику.

Плохо:

```python
@router.post("/projects")
def create_project(...):
    # 100 строк бизнес-логики
```

Лучше:

```python
@router.post("/projects")
def create_project(...):
    return project_service.create(...)
```

---

# 8. Service Layer

Service содержит бизнес-логику.

Например:

```text
ProjectService
AuthService
ProfileService
GitHubService
AIService
```

Service отвечает за:

* бизнес-правила;
* ownership;
* orchestration;
* взаимодействие нескольких repositories;
* работу с внешними сервисами.

---

# 9. Repository Layer

Repository отвечает за работу с базой данных.

Например:

```text
UserRepository
ProjectRepository
TechnologyRepository
```

Repository не должен знать о HTTP.

---

# 10. Pydantic Schemas

Для входных и выходных данных используются отдельные schemas.

Например:

```text
ProjectCreate
ProjectUpdate
ProjectResponse
ProjectPublicResponse
```

Не следует напрямую возвращать SQLAlchemy model наружу.

---

# 11. Database Rules

Используется PostgreSQL.

Все изменения структуры базы данных должны проходить через migrations.

Нельзя изменять production database вручную.

Используется:

```text
Alembic
```

Каждая schema change:

```text
Model change
 ↓
Migration
 ↓
Review
 ↓
Apply
```

---

# 12. IDs

Для основных сущностей использовать единый подход к идентификаторам.

Предпочтительный вариант:

```text
UUID
```

ID не должен зависеть от порядка создания объектов.

---

# 13. Database Transactions

Операции, изменяющие несколько связанных сущностей, должны выполняться транзакционно.

Например:

```text
Create Project
 ↓
Project
 ↓
ProjectTechnology
 ↓
Commit
```

Если часть операции завершилась ошибкой:

```text
Rollback
```

---

# 14. Frontend Rules

Frontend строится на:

```text
React
TypeScript
Vite
```

Основные принципы:

* component-based architecture;
* reusable components;
* typed API;
* разделение UI и бизнес-логики;
* минимизация дублирования.

---

# 15. TypeScript

По возможности не использовать:

```typescript
any
```

Типы должны описывать API responses.

Например:

```typescript
interface Project {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  status: "DRAFT" | "PUBLISHED";
}
```

---

# 16. Components

Компоненты должны быть небольшими и переиспользуемыми.

Плохо:

```text
ProjectPage.tsx
```

с тысячами строк.

Лучше:

```text
ProjectPage
 ├── ProjectHeader
 ├── ProjectDescription
 ├── ProjectTechStack
 ├── ProjectGallery
 └── ProjectActions
```

---

# 17. API Client

Frontend не должен разбросанно создавать fetch-запросы по всему приложению.

Создаётся отдельный API layer:

```text
services/
    api.ts
    auth.ts
    projects.ts
    profile.ts
    github.ts
    ai.ts
```

---

# 18. State Management

Не использовать сложный global state без необходимости.

Сначала использовать:

* React state;
* Context;
* server state подход.

Дополнительная state-management библиотека добавляется только при реальной необходимости.

---

# 19. UI Rules

UI должен быть:

* responsive;
* mobile-first;
* доступным;
* быстрым;
* понятным.

Основные breakpoints должны быть определены централизованно.

---

# 20. Design Principle

Главный визуальный принцип:

> **Минималистичный профессиональный продуктовый интерфейс.**

Портфолио должно выглядеть как настоящий SaaS, а не как учебный проект.

Не использовать:

* чрезмерные градиенты;
* бессмысленные анимации;
* десятки декоративных элементов;
* визуальный шум;
* случайные цвета;
* чрезмерное количество glassmorphism.

---

# 21. Responsive Requirements

Обязательные устройства:

```text
Mobile
Tablet
Desktop
Large Desktop
```

Минимально проверять:

```text
375px
768px
1024px
1440px
```

---

# 22. Authentication

Authentication реализуется на backend.

Frontend не должен самостоятельно считать пользователя авторизованным.

Backend является источником истины.

Protected endpoint:

```text
Authorization
 ↓
Token validation
 ↓
Current user
 ↓
Permission
 ↓
Action
```

---

# 23. Password Security

Пароли никогда не сохраняются в открытом виде.

Используется безопасный password hashing algorithm.

Никогда:

```text
password = "123456"
```

в database.

Только:

```text
password_hash
```

---

# 24. Secrets

API keys и secrets никогда не хранятся:

* в Git;
* в frontend source;
* в README;
* в screenshots;
* в public portfolio.

Используется:

```text
.env
```

Для проекта создаётся:

```text
.env.example
```

без настоящих секретов.

---

# 25. Environment Variables

Пример:

```env
DATABASE_URL=
SECRET_KEY=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
AI_API_KEY=
```

Настоящие значения никогда не коммитятся.

---

# 26. Git Rules

Git используется с самого начала.

Основные branches:

```text
main
develop
feature/*
fix/*
```

Для небольшого проекта допускается упрощённая схема:

```text
main
feature/*
```

---

# 27. Commit Rules

Commit должен описывать конкретное изменение.

Хорошо:

```text
feat: add project creation endpoint
feat: add public portfolio page
fix: validate project ownership
refactor: extract project service
docs: update API specification
```

Плохо:

```text
update
changes
fix
new
test
```

---

# 28. Small Commits

Не следует объединять в один commit:

```text
Backend
Frontend
Database
AI
UI
```

Лучше:

```text
feat: add projects model
feat: add projects API
feat: add project dashboard
feat: add public project page
```

---

# 29. Testing Strategy

Минимальная стратегия:

```text
Unit Tests
Integration Tests
API Tests
Frontend Tests
E2E — optional
```

---

# 30. Backend Tests

Обязательно протестировать:

### Authentication

```text
register
login
invalid password
duplicate email
duplicate username
```

### Projects

```text
create
read
update
delete
publish
unpublish
```

### Authorization

```text
owner can edit
other user cannot edit
```

---

# 31. Public Portfolio Tests

Проверить:

```text
published project visible
draft project invisible
wrong username → 404
wrong slug → 404
```

---

# 32. AI Tests

AI output нельзя считать автоматически корректным.

Проверять:

* response structure;
* required fields;
* maximum lengths;
* invalid AI response;
* timeout;
* provider error.

AI должен быть обёрнут в собственный service layer.

---

# 33. GitHub Tests

Проверить:

```text
valid repository
private repository
repository not found
API rate limit
invalid URL
GitHub unavailable
```

---

# 34. Error Handling

Ошибки должны быть контролируемыми.

Нельзя возвращать пользователю:

```text
Traceback
SQL error
API key
internal path
database details
```

Backend должен возвращать понятную ошибку.

---

# 35. Logging

Логи должны помогать разработчику понять проблему.

Но нельзя логировать:

* passwords;
* tokens;
* API keys;
* sensitive personal data.

Пример:

```text
INFO Project created
INFO User authenticated
WARNING GitHub API rate limit reached
ERROR AI provider unavailable
```

---

# 35.1 Rate Limiting (обновлено 2026-09-16)

Ограничение частоты на auth-эндпоинтах держится на **двух счётчиках**:

1. **На IP** — точное ограничение, пока платформа отдаёт стабильный адрес.
2. **На путь (общий)** — потолок, который держится всегда.

Второй счётчик обязателен, потому что:

* клиент подделывает `X-Forwarded-For` (берётся **правая** запись —
  её дописывает доверенный прокси, левая контролируется клиентом);
* на Render адрес, который видит приложение, оказался **нестабильным**
  между двумя запросами одного клиента — только IP-счётчик там
  фактически вырождается, а потолок по пути держит границу.

Проверка: `backend/tests/test_rate_limit.py` — при подмене `X-Forwarded-For`
перебор всё равно упирается в 429.



Внешние сервисы должны быть изолированы.

Например:

```text
services/
    github_service.py
    ai_service.py
```

Не следует вызывать GitHub API непосредственно из router.

---

# 37. AI Development Rules

AI используется как инструмент разработки.

AI может помогать:

* писать код;
* искать ошибки;
* создавать тесты;
* объяснять код;
* рефакторить;
* создавать документацию.

Но разработчик остаётся ответственным за результат.

---

# 38. AI Code Review Rule

Код, написанный AI, нельзя автоматически считать правильным.

Перед использованием проверить:

```text
1. Architecture
2. Security
3. Logic
4. Dependencies
5. Error handling
6. Performance
7. Tests
```

---

# 39. No Blind Copy-Paste

Запрещено добавлять большой блок AI-generated code без понимания:

* что он делает;
* зачем он нужен;
* какие зависимости использует;
* какие данные получает;
* какие данные изменяет.

---

# 40. AI Agent Rules

Если разработка выполняется AI coding agent, агент обязан:

1. Сначала изучить документацию проекта.
2. Не менять архитектуру без необходимости.
3. Не удалять существующую рабочую функциональность.
4. Не менять API contract без обновления документации.
5. Не добавлять зависимости без причины.
6. Не создавать дублирующие реализации.
7. Не хранить secrets в коде.
8. Не отключать security checks ради прохождения теста.
9. Не удалять тесты только потому, что они мешают.
10. Не считать задачу выполненной только потому, что код компилируется.

---

# 41. Agent Change Protocol

Перед значительным изменением агент должен определить:

```text
What?
Why?
Where?
Impact?
```

После изменения:

```text
Implementation
 ↓
Tests
 ↓
Validation
 ↓
Summary
```

---

# 42. Definition of Done

Функция считается готовой только если:

```text
[ ] Code implemented
[ ] API works
[ ] Database works
[ ] Validation implemented
[ ] Errors handled
[ ] Authentication checked
[ ] Authorization checked
[ ] Tests added
[ ] Existing tests pass
[ ] Frontend integrated
[ ] Responsive behavior checked
[ ] No secrets exposed
```

---

# 43. Feature Completion

Нельзя считать функцию завершённой по принципу:

> "Страница открывается."

Например, Project Creation считается готовым только когда:

```text
Form
 ↓
Validation
 ↓
API
 ↓
Database
 ↓
Response
 ↓
UI update
 ↓
Error handling
```

работают вместе.

---

# 44. No Premature Optimization

Не оптимизировать то, что ещё не стало проблемой.

Сначала:

```text
Correctness
 ↓
Maintainability
 ↓
Security
 ↓
Performance
```

---

# 45. Dependencies

Новая библиотека добавляется только если:

1. она решает конкретную проблему;
2. проблема не решается существующим стеком;
3. библиотека поддерживается;
4. она не создаёт неоправданную сложность.

Не добавлять зависимости:

> "потому что так быстрее написать одну функцию."

---

# 46. Documentation Rule

При существенном изменении:

```text
Architecture
API
Database
Development rules
```

соответствующий документ должен быть обновлён.

Документация не должна расходиться с кодом.

---

# 47. Versioning

API использует:

```text
/api/v1
```

Breaking changes не должны незаметно ломать существующий frontend.

Если API меняется существенно:

```text
v1 → v2
```

либо выполняется controlled migration.

---

# 48. Security Checklist

Перед MVP release:

```text
[ ] Passwords hashed
[ ] Secrets hidden
[ ] Authentication tested
[ ] Authorization tested
[ ] Ownership checks
[ ] Input validation
[ ] File upload validation
[ ] URL validation
[ ] SQL injection protection
[ ] XSS protection
[ ] CORS configured
[ ] Error responses sanitized
[ ] Sensitive logs removed
```

---

# 49. Performance Checklist

Перед deployment:

```text
[ ] Database indexes
[ ] Pagination
[ ] Optimized queries
[ ] Image size limits
[ ] Lazy loading where useful
[ ] Frontend production build
[ ] No unnecessary API requests
[ ] API response size checked
```

---

# 50. Deployment

Production architecture:

```text
Internet
   ↓
Frontend
   ↓
Backend API
   ↓
PostgreSQL
```

External integrations:

```text
Backend
 ├── GitHub API
 └── AI Provider
```

Все secrets хранятся в environment variables.

---

# 51. Docker

Проект должен быть готов к запуску через Docker.

Минимальные containers:

```text
frontend
backend
postgres
```

Для локальной разработки используется:

```text
docker-compose.yml
```

---

# 52. Local Development

Проект должен запускаться локально без ручной настройки десятков компонентов.

Цель:

```text
git clone
 ↓
configure .env
 ↓
docker compose up
 ↓
application works
```

---

# 53. README Requirements

README должен содержать:

```text
Project description
Features
Tech stack
Architecture overview
Installation
Environment variables
Running locally
Testing
API documentation
Deployment
Screenshots
```

---

# 54. Portfolio Presentation

Сам Portfolio Platform является одновременно:

```text
Product
+
Portfolio project
```

Поэтому его публичная страница должна демонстрировать:

* что создано;
* какую проблему решает;
* архитектуру;
* технологии;
* screenshots;
* live demo;
* GitHub;
* ключевые технические решения.

---

# 55. What Not To Build Initially

До завершения MVP НЕ делать:

```text
Custom domains
Payments
Subscriptions
Advanced analytics
Team accounts
Marketplace
Social network
Complex permissions
Mobile app
Browser extension
Advanced AI agents
```

Эти функции могут появиться позже.

---

# 56. MVP Boundary

MVP заканчивается здесь:

```text
Authentication
      ↓
Profile
      ↓
Projects
      ↓
Technologies
      ↓
Publish
      ↓
Public Portfolio
```

Если эти функции работают стабильно — MVP завершён.

---

# 57. Post-MVP

После MVP:

```text
GitHub Import
      ↓
AI Assistant
      ↓
Image Management
      ↓
Themes
      ↓
Analytics
      ↓
Custom Domain
```

Каждая функция добавляется отдельно.

---

# 58. Quality Standard

Проект должен выглядеть не как:

> "учебный проект, созданный для портфолио"

а как:

> **реальный SaaS-продукт, который можно показать клиенту или работодателю.**

Для этого важнее:

```text
Clean architecture
+
Reliable backend
+
Good UX
+
Security
+
Testing
+
Clear documentation
```

чем количество функций.

---

# 59. Final Project Rule

Если возникает вопрос:

> "Добавлять ли эту функцию?"

использовать критерии:

```text
Does it solve a real user problem?
Does it improve the core product?
Does it demonstrate a useful skill?
Does it justify its complexity?
```

Если ответ отрицательный — функцию откладываем.

---

# 60. Final Development Contract

После утверждения четырёх документов проект считается зафиксированным на уровне MVP.

Документы:

```text
00_RESEARCH_METHOD.md
01_PRODUCT_SPEC.md
02_ARCHITECTURE.md
03_DATA_API.md
04_DEVELOPMENT_RULES.md
```

являются источником правил проекта.

При конфликте между:

```text
кодом
```

и

```text
документацией
```

нельзя молча менять одно из них.

Сначала определяется правильное решение, затем обновляется документация или код.

Главная цель:

> **Создать быстрое, качественное и реально работающее портфолио-приложение, которое одновременно является сильным примером full-stack разработки.**
