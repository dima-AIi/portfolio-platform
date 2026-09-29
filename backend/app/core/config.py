from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Shipping this value unchanged means anyone can sign a session cookie for any
# user id, so it must never survive a production boot.
PLACEHOLDER_JWT_SECRET = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "production"
    DATABASE_URL: str = "sqlite:///./app.db"
    JWT_SECRET: str = PLACEHOLDER_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    PASSWORD_RESET_TTL_MINUTES: int = 15
    # Public base URL of the frontend. Used to build absolute URLs for the
    # sitemap and Open Graph tags, which must be absolute to be crawlable.
    PUBLIC_URL: str = "http://localhost:5173"

    # SMTP (optional). When not configured, reset codes are returned in the API
    # response in development mode instead of being emailed.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_TLS: bool = True

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)

    @model_validator(mode="after")
    def _reject_placeholder_secret(self) -> "Settings":
        """Fail fast rather than sign sessions with a public key.

        ENV defaults to "production", so a deployment that forgets JWT_SECRET
        would otherwise boot happily and accept a hand-crafted cookie for any
        user id. Refusing to start is the only safe outcome.
        """
        if self.ENV == "production" and self.JWT_SECRET == PLACEHOLDER_JWT_SECRET:
            raise ValueError(
                "JWT_SECRET is still the placeholder value while ENV=production. "
                "Set a random secret before starting the server: "
                'python -c "import secrets; print(secrets.token_hex(32))"'
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
