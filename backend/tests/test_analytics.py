"""Tests for traffic analytics and the owner data export."""

from app.utils.analytics import browser_family, classify_referrer


def test_classify_referrer_known_sources():
    assert classify_referrer("https://t.me/channel/123") == "Telegram"
    assert classify_referrer("https://github.com/someone") == "GitHub"
    assert classify_referrer("https://www.google.com/search?q=portfolio") == "Google"


def test_classify_referrer_keeps_hacker_news_distinct_from_generic():
    assert classify_referrer("https://news.ycombinator.com/item?id=1") == "Hacker News"


def test_classify_referrer_direct_when_absent():
    assert classify_referrer(None) == "Прямые заходы"
    assert classify_referrer("") == "Прямые заходы"


def test_classify_referrer_drops_path_so_history_cannot_be_rebuilt():
    """An unknown host must not be stored with its query or path."""
    label = classify_referrer("https://secret-search.example.com/path?query=private")
    assert "secret-search" not in label
    assert "query" not in label
    assert "path" not in label


def test_browser_family_is_coarse():
    assert browser_family("Mozilla/5.0 Chrome/120.0") == "Chrome"
    assert browser_family("Mozilla/5.0 Firefox/121.0") == "Firefox"
    assert browser_family(None) is None


def test_analytics_records_a_view_with_referrer(client, auth_headers):
    client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "strongpass123"})
    project = client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"title": "Кейс", "short_description": "Описание"},
    )
    assert project.status_code == 201, project.text

    resp = client.get(
        "/api/v1/public/owner",
        headers={"Referer": "https://t.me/durov"},
    )
    assert resp.status_code == 200

    analytics = client.get("/api/v1/analytics", headers=auth_headers)
    assert analytics.status_code == 200, analytics.text
    data = analytics.json()
    assert data["total_views"] >= 1
    sources = {s["source"]: s["views"] for s in data["sources"]}
    assert sources.get("Telegram", 0) >= 1
    # The daily series must be a fixed window with no gaps.
    assert len(data["daily"]) == 14


def test_export_contains_profile_and_projects(client, auth_headers):
    client.put(
        "/api/v1/profile",
        headers=auth_headers,
        json={"display_name": "Дмитрий К.", "headline": "Full-Stack"},
    )
    client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"title": "ELORA", "short_description": "Запись в студию"},
    )

    resp = client.get("/api/v1/export", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert "attachment" in resp.headers.get("content-disposition", "")

    data = resp.json()
    assert data["format"] == "portfolio-platform-export"
    assert data["account"]["username"] == "owner"
    assert data["profile"]["display_name"] == "Дмитрий К."
    assert data["projects"][0]["title"] == "ELORA"


def test_export_and_analytics_require_auth(client):
    assert client.get("/api/v1/export").status_code == 401
    assert client.get("/api/v1/analytics").status_code == 401


def test_export_does_not_leak_another_account(client, auth_headers, second_user_headers):
    """Each account's export must contain only its own content."""
    client.put("/api/v1/profile", headers=auth_headers, json={"display_name": "Первый"})
    client.put("/api/v1/profile", headers=second_user_headers, json={"display_name": "Второй"})

    data = client.get("/api/v1/export", headers=auth_headers).json()
    assert data["profile"]["display_name"] == "Первый"
    assert data["account"]["username"] == "owner"
