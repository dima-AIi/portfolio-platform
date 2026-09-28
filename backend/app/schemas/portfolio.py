
from pydantic import BaseModel, ConfigDict

from app.schemas.profile import ProfileResponse
from app.schemas.project import ProjectResponse


class PublicPortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    profile: ProfileResponse
    projects: list[ProjectResponse]
    skills: list[str] = []
    # Pagination metadata. `total` counts every published project, so a client
    # can tell whether a "load more" control is needed.
    total: int = 0
    page: int | None = None
    limit: int | None = None


class PublicProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    theme: str = "classic"
    project: ProjectResponse
