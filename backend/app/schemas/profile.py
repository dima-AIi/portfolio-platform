import uuid

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    headline: str | None = Field(default=None, max_length=160)
    bio: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=120)
    website_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    linkedin_url: HttpUrl | None = None
    telegram_url: HttpUrl | None = None
    theme: str | None = Field(default=None, pattern="^(classic|dark|minimal)$")

    model_config = ConfigDict(str_strip_whitespace=True)


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str | None
    headline: str | None
    bio: str | None
    avatar_url: str | None
    location: str | None
    website_url: str | None
    github_url: str | None
    linkedin_url: str | None
    telegram_url: str | None
    theme: str = "classic"
    view_count: int = 0


class AvatarResponse(BaseModel):
    avatar_url: str
