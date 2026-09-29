from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Response

from app.core.config import settings
from app.utils.errors import AppError
from app.utils.password_strength import BCRYPT_MAX_BYTES

# Name of the session cookie. httpOnly keeps the token out of reach of any
# JavaScript on the page, so an XSS bug can no longer exfiltrate the session.
SESSION_COOKIE_NAME = "portfolio_session"


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) > BCRYPT_MAX_BYTES:
        # bcrypt 5 raises here. Request schemas already reject such passwords,
        # so reaching this point means a caller bypassed validation; fail loudly
        # instead of silently truncating, which would make two different
        # passwords that share a 72-byte prefix interchangeable.
        raise AppError(
            "PASSWORD_TOO_LONG",
            f"Пароль слишком длинный: максимум {BCRYPT_MAX_BYTES} байт.",
            422,
        )
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Return user_id from token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def set_session_cookie(response: Response, token: str) -> None:
    """Attach the session token as a cookie.

    SameSite=Lax is the CSRF defence: browsers do not attach these cookies to
    cross-site POST/PUT/DELETE requests, so a hostile page cannot drive an
    authenticated state change. `secure` is required in production and ignored
    on plain http://localhost during development.
    """
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
