"""Create or refresh the owner's real portfolio account.

Built for the case where the showcase account is no longer wanted and the
public page should belong to a real person instead. Credentials are read
from the environment so a password never reaches the repository:

    set SEED_EMAIL=zavtrawes@gmail.com
    set SEED_USERNAME=zavtrawes
    set SEED_PASSWORD=...
    set SEED_BASE=https://portfolio-backend-rdaw.onrender.com
    python scripts/seed_owner_portfolio.py

SEED_BASE defaults to http://localhost:8000. Re-running is safe: an
existing project with the same title is updated rather than duplicated.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from typing import NamedTuple

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.environ.get("SEED_BASE", "http://localhost:8000").rstrip("/") + "/api/v1"
EMAIL = os.environ.get("SEED_EMAIL", "").strip()
USERNAME = os.environ.get("SEED_USERNAME", "").strip()
PASSWORD = os.environ.get("SEED_PASSWORD", "")

ELORA_URL = "https://elora2026.runasp.net"
DISPLAY_NAME = "Дмитрий"
GITHUB_URL = "https://github.com/dima-Ai"

COVER_IMAGE = f"{ELORA_URL}/images/og-cover.jpg"
GALLERY_IMAGES = [
    f"{ELORA_URL}/images/hero/hero.jpg",
    f"{ELORA_URL}/images/promo/promo.jpg",
    f"{ELORA_URL}/images/works/manicure-01.jpg",
    f"{ELORA_URL}/images/works/lashes-01.jpg",
]
PROJECT_TECHNOLOGIES = [
    "C#", "ASP.NET Core", "HTML/CSS", "JavaScript", "PostgreSQL", "PWA", "SEO",
]

PROFILE = {
    "display_name": DISPLAY_NAME,
    "headline": "Full-Stack разработчик",
    "bio": (
        "Разрабатываю веб-сервисы, которые решают конкретную задачу бизнеса. "
        "Каждый проект показываю как кейс: проблема, решение, результат и стек. "
        "Из последнего — онлайн-запись для студии красоты ELORA."
    ),
    "location": "Москва",
    "website_url": ELORA_URL,
    "github_url": GITHUB_URL,
    # No public Telegram handle — omitting the field hides the button instead
    # of rendering a link that goes nowhere.
    "telegram_url": None,
    "theme": "classic",
}


class Response(NamedTuple):
    status: int
    data: object
    set_cookie: str = ""


def call(method: str, path: str, token: str | None = None, body: dict | None = None):
    """Perform a request.

    The session JWT arrives in an httpOnly cookie; this script is not a
    browser, so it replays the cookie value as an Authorization header.
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
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = resp.read()
            cookie = resp.headers.get("set-cookie", "")
            return Response(resp.status, json.loads(payload) if payload else None, cookie)
    except urllib.error.HTTPError as e:
        payload = e.read()
        cookie = e.headers.get("set-cookie", "")
        return Response(e.code, json.loads(payload) if payload else None, cookie)
    except urllib.error.URLError as e:
        # A refused connection means the API is not reachable (wrong SEED_BASE,
        # backend not started). Say so instead of dumping a traceback.
        print(f"FAIL: cannot reach {BASE} — {e.reason}")
        print("Start the backend, or point SEED_BASE at the right host.")
        sys.exit(1)


def session_token(result) -> str:
    for part in result.set_cookie.split(";"):
        if part.strip().startswith("portfolio_session="):
            return part.split("=", 1)[1]
    return ""


def download(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return resp.read()
    except Exception as exc:  # noqa: BLE001 - a dead screenshot must not abort the run
        print(f"  WARN could not fetch {url}: {exc}")
        return None


def upload_image(path: str, token: str, content: bytes) -> dict | None:
    boundary = "----OwnerSeed4b9c"
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"  WARN upload failed ({exc.code}) for {path}")
        return None


def ensure_account() -> str:
    result = call("POST", "/auth/register", body={
        "email": EMAIL, "username": USERNAME, "password": PASSWORD})
    if result.status == 409:
        payload = result.data if isinstance(result.data, dict) else {}
        code = (payload.get("error") or {}).get("code")
        if code == "USERNAME_ALREADY_EXISTS":
            print(
                f"FAIL: username '{USERNAME}' is taken by a different account.\n"
                "Pick another SEED_USERNAME, or remove the existing account "
                "with scripts/remove_accounts.py."
            )
            sys.exit(1)
        result = call("POST", "/auth/login", body={
            "email": EMAIL, "password": PASSWORD})
    if result.status not in (200, 201):
        print(f"FAIL auth: {result.status} {result.data}")
        sys.exit(1)
    token = session_token(result)
    if not token:
        print("FAIL auth: no session cookie in response")
        sys.exit(1)
    print(f"auth OK as @{USERNAME}")
    return token


PROJECT_TITLE = "ELORA — онлайн-запись в студию красоты"

ELORA_PROJECT = {
    "title": PROJECT_TITLE,
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
    missing = [
        name for name, value in
        (("SEED_EMAIL", EMAIL), ("SEED_USERNAME", USERNAME), ("SEED_PASSWORD", PASSWORD))
        if not value
    ]
    if missing:
        print("FAIL: set the environment variables first: " + ", ".join(missing))
        return 1

    print("== Account ==")
    token = ensure_account()

    print("== Profile ==")
    status = call("PUT", "/profile", token, PROFILE).status
    print(f"  {'OK' if status == 200 else 'FAIL'} profile -> {status}")

    print("== Project ==")
    existing = call("GET", "/projects", token).data
    items = existing.get("items", []) if isinstance(existing, dict) else []
    match = next((p for p in items if p["title"] == PROJECT_TITLE), None)

    if match:
        status = call("PUT", f"/projects/{match['id']}", token, ELORA_PROJECT).status
        print(f"  {'OK' if status == 200 else 'FAIL'} updated {match['id']}")
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
    print("Portfolio ready:")
    print(f"  public page   {BASE.split('/api')[0]}/{USERNAME}")
    print(f"  login         {EMAIL}")
    print("  (the password is the SEED_PASSWORD you set — it is never printed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

