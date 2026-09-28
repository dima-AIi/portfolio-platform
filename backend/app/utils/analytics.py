"""Traffic analytics for public portfolio and case-study pages.

The per-page view_count columns answer "how often" but not "from where".
This records one row per view with a coarse referrer bucket so the owner can
see which case study actually gets opened and which channel brings visitors.

Privacy: no IP addresses, no cookies, no user identifiers. The referrer is
reduced to a small set of known sources and anything unrecognised is dropped
rather than stored raw, so a full browsing history cannot be reconstructed.
"""

from urllib.parse import urlparse

# Host fragment -> bucket. Ordered longest-first at match time so that
# "news.ycombinator.com" is not swallowed by a bare "ycombinator.com" rule.
KNOWN_REFERRERS: dict[str, str] = {
    "t.me": "Telegram",
    "telegram.me": "Telegram",
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "linkedin.com": "LinkedIn",
    "hh.ru": "HeadHunter",
    "habr.com": "Habr",
    "vc.ru": "VC.ru",
    "pikabu.ru": "Pikabu",
    "google.": "Google",
    "bing.com": "Bing",
    "yandex.": "Яндекс",
    "mail.ru": "Mail.ru",
    "news.ycombinator.com": "Hacker News",
    "reddit.com": "Reddit",
    "twitter.com": "X (Twitter)",
    "x.com": "X (Twitter)",
    "dzen.ru": "Дзен",
}

DIRECT = "Прямые заходы"


def classify_referrer(referrer: str | None) -> str:
    """Reduce a Referer header to a short, non-identifying bucket."""
    if not referrer:
        return DIRECT
    host = (urlparse(referrer).hostname or "").lower()
    if not host:
        return DIRECT
    for needle, label in KNOWN_REFERRERS.items():
        if needle in host:
            return label
    # Unknown host: keep the registrable-ish label but never the full URL,
    # which could embed a private path or a search query.
    return host.split(".")[-2] if host.count(".") >= 2 else host


def browser_family(user_agent: str | None) -> str | None:
    """Coarse browser name, used only to compare desktop vs mobile traffic."""
    if not user_agent:
        return None
    ua = user_agent.lower()
    for needle, label in (
        ("edg/", "Edge"),
        ("chrome", "Chrome"),
        ("safari", "Safari"),
        ("firefox", "Firefox"),
        ("yabrowser", "Яндекс.Браузер"),
    ):
        if needle in ua:
            return label
    return "Другой"
