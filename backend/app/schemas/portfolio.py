
from pydantic import BaseModel, ConfigDict

from app.schemas.profile import ProfileResponse
from app.schemas.project import ProjectResponse


class PublicPortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    profile: ProfileResponse
    projects: list[ProjectResponse]
    skills: list[str] = []


class PublicProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    theme: str = "classic"
    project: ProjectResponse
