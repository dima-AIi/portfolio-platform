"""Seed the showcase portfolio: a filled public page visitors can actually open.

The ELORA case study documents a real deployed project — an online booking
service for a beauty studio — in the Problem -> Solution -> Result -> Stack
shape this platform is built around. Screenshots are pulled from the live
site so the showcase shows the real thing, not a mockup.

Run with the backend already running on localhost:8000:
    python scripts/seed_showcase.py
"""

import json
import sys
import urllib.error
import urllib.request
from typing import NamedTuple

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000") + "/api/v1"

DEMO_EMAIL = "demo@portfolio-platform.dev"
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "showcase-2026"

ELORA_URL = "https://elora2026.runasp.net"
COVER_IMAGE = f"{ELORA_URL}/images/og-cover.jpg"
GALLERY_IMAGES = [
    f"{ELORA_URL}/images/hero/hero.jpg",
    f"{ELORA_URL}/images/promo/promo.jpg",
    f"{ELORA_URL}/images/works/manicure-01.jpg",
    f"{ELORA_URL}/images/works/lashes-01.jpg",
]
PROJECT_TECHNOLOGIES = ["C#", "ASP.NET Core", "HTML/CSS", "JavaScript", "PostgreSQL", "PWA", "SEO"]

PROFILE = {
    "display_name": "Александр И.",
    "headline": "Full-Stack разработчик",
    "bio": (
        "Собираю веб-сервисы, которые решают конкретную задачу бизнеса: "
        "от записи клиентов до внутренних инструментов. Каждый проект "
        "показываю через кейс — проблема, решение, результат."
    ),
    "location": "Москва",
    "website_url": ELORA_URL,
    "github_url": "https://github.com/example",
    "telegram_url": "https://t.me/example",
    "theme": "classic",
}


class Response(NamedTuple):
    status: int
    data: object
    set_cookie: str = ""


def call(method: str, path: str, token: str | None = None, body: dict | None = None):
    """Perform a request.

    The session JWT arrives in an httpOnly cookie; this script is not a browser,
    so it replays the cookie value as an Authorization header.
    """
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read()
            cookie = resp.headers.get("set-cookie", "")
            return Response(resp.status, json.loads(payload) if payload else None, cookie)
    except urllib.error.HTTPError as e:
        payload = e.read()
        cookie = e.headers.get("set-cookie", "")
        return Response(e.code, json.loads(payload) if payload else None, cookie)


def session_token(result) -> str:
    for part in result.set_cookie.split(";"):
        if part.strip().startswith("portfolio_session="):
            return part.split("=", 1)[1]
    return ""


def download(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read()
    except Exception as exc:  # noqa: BLE001 - a dead screenshot must not abort the seed
        print(f"  WARN could not fetch {url}: {exc}")
        return None


def upload_image(path: str, token: str, content: bytes) -> dict | None:
    boundary = "----ShowcaseSeed5a1b"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="shot.jpg"\r\n'
        "Content-Type: image/jpeg\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"  WARN upload failed ({exc.code}) for {path}")
        return None


def ensure_account() -> str:
    result = call("POST", "/auth/register", body={
        "email": DEMO_EMAIL, "username": DEMO_USERNAME, "password": DEMO_PASSWORD})
    if result.status == 409:
        result = call("POST", "/auth/login", body={
            "email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    if result.status not in (200, 201):
        print(f"FAIL auth: {result.status} {result.data}")
        sys.exit(1)
    token = session_token(result)
    if not token:
        print("FAIL auth: no session cookie in response")
        sys.exit(1)
    print(f"auth OK as @{DEMO_USERNAME}")
    return token


ELORA_PROJECT = {
    "title": "ELORA — онлайн-запись в студию красоты",
    "short_description": (
        "Сервис онлайн-записи для салона: 24 услуги, бронирование слотов "
        "без пересечений, личный кабинет и PWA."
    ),
    "problem": (
        "Небольшая студия красоты принимала записи только по телефону и в переписке. "
        "Это приводило к трём проблемам:\n"
        "• Клиент тратил время на ожидание ответа и уточнение свободного времени.\n"
        "• Администратор вручную сверял расписание, из-за чего возникали пересечения "
        "и двойные записи на один слот.\n"
        "• У студии не было единой страницы с услугами, ценами и работами мастеров — "
        "новый клиент не мог оценить качество до записи."
    ),
    "solution": (
        "Спроектировал и собрал серверное веб-приложение на ASP.NET Core "
        "с полноценной онлайн-записью.\n"
        "Что реализовано:\n"
        "• Каталог из 24 услуг в 6 направлениях с ценами и длительностью.\n"
        "• Запись в 8 шагов: услуга → мастер → дата → время → имя → телефон → "
        "Telegram → подтверждение.\n"
        "• Серверный расчёт свободных слотов по расписанию мастера и уже занятым "
        "записям — один слот всегда принадлежит одному клиенту.\n"
        "• Личный кабинет «Мои записи» с историей визитов.\n"
        "• Галерея работ с фильтром по направлению.\n"
        "• PWA: устанавливается на телефон и работает как приложение.\n"
        "• SEO-разметка Open Graph, canonical и sitemap для индексации."
    ),
    "features": (
        "• 8-шаговая запись с валидацией на каждом шаге\n"
        "• Серверный контроль пересечений слотов\n"
        "• Каталог услуг с ценами и фильтрами\n"
        "• Галерея работ с фильтром по категориям\n"
        "• Личный кабинет с историей записей\n"
        "• PWA с офлайн-оболочкой и манифестом\n"
        "• FAQ, прайс-лист, страницы правил и обработки данных\n"
        "• Адаптивная вёрстка и поддержка prefers-reduced-motion"
    ),
    "result": (
        "Проект опубликован и доступен по постоянной ссылке: " + ELORA_URL + "\n"
        "Что получилось:\n"
        "• Запись занимает около минуты и не требует звонков.\n"
        "• Пересечения записей исключены на уровне сервера, а не ручной сверкой.\n"
        "• 14 работ в галерее показывают качество до первого визита.\n"
        "• Сайт устанавливается на смартфон как приложение.\n"
        "• Полная SEO-разметка для поиска и репостов в мессенджерах."
    ),
    "role": "Full-Stack разработчик: проектирование, вёрстка, серверная логика",
    "live_url": ELORA_URL,
}


def main() -> int:
    print("== Seed showcase portfolio ==")
    token = ensure_account()

    print("== Profile ==")
    status = call("PUT", "/profile", token, PROFILE).status
    print(f"  {'OK' if status == 200 else 'FAIL'} profile -> {status}")

    print("== Project ==")
    existing = call("GET", "/projects", token).data
    items = existing.get("items", []) if isinstance(existing, dict) else []
    match = next((p for p in items if p["title"] == ELORA_PROJECT["title"]), None)

    if match:
        # Refresh the copy so re-running the seed picks up edited case text.
        status = call("PUT", f"/projects/{match['id']}", token, ELORA_PROJECT).status
        print(f"  {'OK' if status == 200 else 'FAIL'} updated existing {match['id']}")
        project = match
    else:
        result = call("POST", "/projects", token, ELORA_PROJECT)
        if result.status != 201:
            print(f"  FAIL create -> {result.status} {result.data}")
            return 1
        project = result.data
        print(f"  created {project['id']} ({project['slug']})")

    print("== Technologies ==")
    techs = call("GET", "/technologies").data
    wanted = [t["id"] for t in techs if t["name"] in PROJECT_TECHNOLOGIES]
    status = call("PUT", f"/projects/{project['id']}/technologies", token,
                  {"technology_ids": wanted}).status
    print(f"  {'OK' if status == 200 else 'FAIL'} technologies -> {status} ({len(wanted)})")

    if not project.get("images"):
        print("== Images ==")
        cover = download(COVER_IMAGE)
        if cover:
            uploaded = upload_image(f"/projects/{project['id']}/images", token, cover)
            if uploaded:
                status = call("PUT", f"/projects/{project['id']}", token,
                              {"cover_image_url": uploaded["url"]}).status
                print(f"  {'OK' if status == 200 else 'FAIL'} cover")
        for url in GALLERY_IMAGES:
            content = download(url)
            if content and upload_image(f"/projects/{project['id']}/images", token, content):
                print(f"  OK {url.rsplit('/', 1)[-1]}")
    else:
        print("== Images ==\n  already uploaded, skipping")

    print("== Publish ==")
    status = call("POST", f"/projects/{project['id']}/publish", token).status
    print(f"  {'OK' if status == 200 else 'FAIL'} publish -> {status}")

    print()
    print(f"Showcase ready: /{DEMO_USERNAME}")
    print(f"Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
