import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

ProjectStatus = Literal["DRAFT", "PUBLISHED"]


class ProjectTechnologySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    category: str | None


class ProjectImageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    alt_text: str | None
    sort_order: int


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    short_description: str | None = Field(default=None, max_length=300)
    problem: str | None = Field(default=None, max_length=5000)
    solution: str | None = Field(default=None, max_length=5000)
    features: str | None = Field(default=None, max_length=5000)
    result: str | None = Field(default=None, max_length=5000)
    role: str | None = Field(default=None, max_length=120)
    github_url: HttpUrl | None = None
    live_url: HttpUrl | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class ProjectUpdate(ProjectCreate):
    title: str | None = Field(default=None, max_length=120)
    cover_image_url: str | None = Field(default=None, max_length=500)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    short_description: str | None
    problem: str | None
    solution: str | None
    features: str | None
    result: str | None
    role: str | None
    cover_image_url: str | None
    github_url: str | None
    live_url: str | None
    status: ProjectStatus
    sort_order: int
    view_count: int = 0
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    technologies: list[ProjectTechnologySchema] = []
    images: list[ProjectImageSchema] = []


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int | None = None
    limit: int | None = None


class ProjectReorderRequest(BaseModel):
    project_ids: list[uuid.UUID] = Field(min_length=1)


class ProjectTechnologiesRequest(BaseModel):
    technology_ids: list[uuid.UUID] = Field(max_length=50)
