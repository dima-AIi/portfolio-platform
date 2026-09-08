"""Seed a demo user with a filled portfolio.

Run with the backend server already running on localhost:8000:
    python scripts/seed_demo.py
"""

import io
import json
import struct
import sys
import urllib.request
import zlib

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000") + "/api/v1"


def png_bytes(width: int, height: int, top_rgb, bottom_rgb) -> bytes:
    """Generate a simple vertical-gradient PNG with pure stdlib."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    rows = bytearray()
    for y in range(height):
        rows.append(0)  # filter: none
        t = y / max(height - 1, 1)
        r = int(top_rgb[0] + (bottom_rgb[0] - top_rgb[0]) * t)
        g = int(top_rgb[1] + (bottom_rgb[1] - top_rgb[1]) * t)
        b = int(top_rgb[2] + (bottom_rgb[2] - top_rgb[2]) * t)
        rows.extend(struct.pack("BBB", r, g, b) * width)
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            chunk(b"IDAT", zlib.compress(bytes(rows))),
            chunk(b"IEND", b""),
        ]
    )


def call(method: str, path: str, token: str | None = None, body: dict | None = None):
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
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = resp.read()
            return resp.status, json.loads(payload) if payload else None
    except urllib.error.HTTPError as e:
        payload = e.read()
        return e.code, json.loads(payload) if payload else None


def upload(path: str, token: str, filename: str, content: bytes):
    boundary = "----SeedBoundary7d1a2c"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: image/png\r\n\r\n"
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
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


PROJECTS = [
    {
        "title": "Telegram CRM",
        "short_description": "CRM-система для бизнеса в Telegram.",
        "problem": "Небольшая онлайн-школа вела заявки учеников вручную в переписках Telegram. "
        "Часть обращений терялась, менеджеры отвечали с задержкой в несколько часов.",
        "solution": "Разработал централизованную CRM с Telegram-ботом для приёма заявок, "
        "воронкой сделок и автоматическими уведомлениями менеджерам. "
        "Бэкенд — FastAPI, админка — React.",
        "role": "Full-Stack разработчик (соло-проект)",
        "features": "Бот приёма заявок с инлайн-кнопками\nВоронка сделок (новая / в работе / успешна)\n"
        "Уведомления менеджерам\nАдмин-панель со статистикой",
        "result": "Время ответа на заявку сократилось с часов до минут; все обращения "
        "хранятся в одной системе вместо истории чатов.",
        "github_url": "https://github.com/example/telegram-crm",
        "live_url": "https://telegram-crm.example.com",
        "technologies": ["Python", "FastAPI", "PostgreSQL", "React"],
        "cover": (600, 400, (79, 70, 229), (129, 140, 248)),
    },
    {
        "title": "Analytics Dashboard",
        "short_description": "Дашборд аналитики для интернет-магазинов в реальном времени.",
        "problem": "Владельцы магазинов не могли быстро увидеть динамику продаж — данные "
        "были разбросаны между платёжными системами и Excel-таблицами.",
        "solution": "Разработал дашборд с интерактивными графиками, фильтрами по периоду "
        "и категориям товаров, экспортом в CSV. Агрегация данных на бэкенде с кэшированием.",
        "role": "Frontend-разработчик",
        "features": "Интерактивные графики продаж\nФильтры по периоду и категориям\n"
        "Экспорт в CSV\nТёмная тема",
        "result": "Владельцы видят продажи за день на одном экране вместо ручного сведения таблиц.",
        "github_url": "https://github.com/example/analytics-dashboard",
        "live_url": "https://analytics.example.com",
        "technologies": ["TypeScript", "React", "PostgreSQL", "Tailwind CSS"],
        "cover": (600, 400, (5, 150, 105), (16, 185, 129)),
    },
    {
        "title": "Автоматизатор рутины",
        "short_description": "Telegram-бот, автоматизирующий рутинные операции с файлами.",
        "problem": "Команда ежедневно вручную переименовывала, конвертировала и архивировала "
        "десятки файлов, тратя на это около 40 минут в день.",
        "solution": "Бот, который принимает файлы, применяет правила обработки "
        "(шаблоны переименования, конвертация форматов, упаковка в архив) "
        "и возвращает готовые архивы.",
        "role": "Backend-разработчик (соло-проект)",
        "features": "Обработка файлов по правилам\nУпаковка в архив\nИстория обработок",
        "result": "Ежедневная рутинная работа с файлами сократилась с ~40 минут до менее двух минут.",
        "github_url": "https://github.com/example/task-automator",
        "live_url": None,
        "technologies": ["Python", "Telegram Bot API", "SQLite"],
        "cover": (600, 400, (217, 119, 6), (245, 158, 11)),
    },
]


def main() -> int:
    print("== Seed demo user ==")

    status, data = call("POST", "/auth/register", body={
        "email": "demo@example.com", "username": "demo", "password": "demo12345"})
    if status == 409:
        status, data = call("POST", "/auth/login", body={
            "email": "demo@example.com", "password": "demo12345"})
    if status not in (200, 201):
        print(f"FAIL auth: {status} {data}")
        return 1
    token = data["access_token"]
    print("auth OK")

    status, _ = call("PUT", "/profile", token, {
        "display_name": "Дмитрий К.",
        "headline": "Full-Stack разработчик",
        "bio": "Разрабатываю инструменты автоматизации и веб-приложения. "
               "Люблю превращать запутанные ручные процессы в работающие продукты.",
        "location": "Москва",
        "website_url": "https://dmitriy.example.com",
        "github_url": "https://github.com/example",
        "telegram_url": "https://t.me/example",
    })
    print("profile:", "OK" if status == 200 else f"FAIL {status}")

    techs = call("GET", "/technologies")[1]
    tech_by_name = {t["name"]: t["id"] for t in techs}

    existing = call("GET", "/projects", token)[1]
    existing_titles = {p["title"] for p in existing["items"]}

    for project in PROJECTS:
        if project["title"] in existing_titles:
            print(f"project '{project['title']}': already exists, skip")
            continue
        status, created = call("POST", "/projects", token, {
            "title": project["title"],
            "short_description": project["short_description"],
            "problem": project["problem"],
            "solution": project["solution"],
            "features": project["features"],
            "result": project["result"],
            "role": project["role"],
            "github_url": project["github_url"],
            "live_url": project["live_url"],
        })
        if status != 201:
            print(f"project '{project['title']}': FAIL {status} {created}")
            continue
        tech_ids = [tech_by_name[n] for n in project["technologies"] if n in tech_by_name]
        call("PUT", f"/projects/{created['id']}/technologies", token,
             {"technology_ids": tech_ids})
        w, h, top, bottom = project["cover"]
        upload(f"/projects/{created['id']}/images", token,
               f"{created['slug']}-cover.png", png_bytes(w, h, top, bottom))
        cover_url = call("GET", f"/projects/{created['id']}", token)[1]["images"][0]["url"]
        call("PUT", f"/projects/{created['id']}", token, {"cover_image_url": cover_url})
        call("POST", f"/projects/{created['id']}/publish", token)
        print(f"project '{project['title']}': created + published")

    print()
    print("Demo account ready:")
    print("  login:    demo@example.com / demo12345")
    print("  dashboard http://localhost:5173/dashboard")
    print("  public    http://localhost:5173/demo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
