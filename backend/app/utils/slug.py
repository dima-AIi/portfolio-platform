import re
import uuid

# Must stay in sync with the routes the SPA owns (frontend/src/app/AppRoutes.tsx).
# Every top-level path listed there wins over "/:username", so a portfolio with
# one of these names could be created but would never be reachable.
RESERVED_USERNAMES = {
    "login", "register", "dashboard", "api", "admin", "settings",
    "public", "uploads", "static", "assets", "logout", "profile",
    "projects", "portfolio", "docs", "openapi.json", "health",
    "forgot-password", "forgot_password",
}

USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,29}$")


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_RE.match(username)) and username not in RESERVED_USERNAMES


TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e",
    "ю": "yu", "я": "ya",
}


def slugify(text: str) -> str:
    slug = text.strip().lower()
    slug = "".join(TRANSLIT.get(ch, ch) for ch in slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug


def unique_slug(base: str, existing: set[str]) -> str:
    slug = base or "project"
    candidate = slug
    counter = 2
    while candidate in existing:
        candidate = f"{slug}-{counter}"
        counter += 1
    return candidate


def random_filename(extension: str) -> str:
    return f"{uuid.uuid4().hex}{extension}"
