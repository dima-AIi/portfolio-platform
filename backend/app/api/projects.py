import uuid

from fastapi import APIRouter, Depends, Query

from app.api.auth import get_current_user
from app.models import User
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectReorderRequest,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
def list_projects(
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(),
) -> ProjectListResponse:
    return service.list_projects(current_user.id, page, limit)


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(),
) -> ProjectResponse:
    return service.create_project(current_user.id, data)


@router.put("/reorder", response_model=None, status_code=204)
def reorder_projects(
    data: ProjectReorderRequest,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(),
) -> None:
    # NOTE: declared before /{project_id} so "reorder" is not treated as an id.
    service.reorder_projects(current_user.id, data.project_ids)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(),
) -> ProjectResponse:
    return service.get_project(current_user.id, project_id)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(),
) -> ProjectResponse:
    return service.update_project(current_user.id, project_id, data)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(),
) -> None:
    service.delete_project(current_user.id, project_id)


@router.post("/{project_id}/publish", response_model=ProjectResponse)
def publish_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(),
) -> ProjectResponse:
    return service.publish_project(current_user.id, project_id)


@router.post("/{project_id}/unpublish", response_model=ProjectResponse)
def unpublish_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProjectService = Depends(),
) -> ProjectResponse:
    return service.unpublish_project(current_user.id, project_id)
