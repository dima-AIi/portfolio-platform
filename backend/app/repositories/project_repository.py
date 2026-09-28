import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import STATUS_PUBLISHED, Project, ProjectImage, Technology


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def _query(self):
        return (
            select(Project)
            .options(selectinload(Project.technologies), selectinload(Project.images))
        )

    def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        return self.db.scalar(self._query().where(Project.id == project_id))

    def get_by_id_and_user(self, project_id: uuid.UUID, user_id: uuid.UUID) -> Project | None:
        return self.db.scalar(
            self._query().where(Project.id == project_id, Project.user_id == user_id)
        )

    def list_by_user(
        self,
        user_id: uuid.UUID,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Project]:
        stmt = (
            self._query()
            .where(Project.user_id == user_id)
            .order_by(Project.sort_order, Project.created_at)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        return list(self.db.scalars(stmt).all())

    def list_published_by_user(self, user_id: uuid.UUID) -> list[Project]:
        stmt = (
            self._query()
            .where(Project.user_id == user_id, Project.status == STATUS_PUBLISHED)
            .order_by(Project.sort_order, Project.published_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def count_by_user(self, user_id: uuid.UUID) -> int:
        return self.db.scalar(
            select(func.count()).select_from(Project).where(Project.user_id == user_id)
        ) or 0

    def existing_slugs(self, user_id: uuid.UUID, exclude_id: uuid.UUID | None = None) -> set[str]:
        stmt = select(Project.slug).where(Project.user_id == user_id)
        if exclude_id:
            stmt = stmt.where(Project.id != exclude_id)
        return set(self.db.scalars(stmt).all())

    def create(self, user_id: uuid.UUID, **fields) -> Project:
        project = Project(user_id=user_id, **fields)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def save(self, project: Project) -> Project:
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.commit()

    def set_technologies(self, project: Project, technology_ids: list[uuid.UUID]) -> Project:
        techs = (
            self.db.scalars(select(Technology).where(Technology.id.in_(technology_ids))).all()
            if technology_ids
            else []
        )
        project.technologies = list(techs)
        self.db.commit()
        self.db.refresh(project)
        return project

    def reorder(self, user_id: uuid.UUID, ordered_ids: list[uuid.UUID]) -> None:
        projects = {
            p.id: p for p in self.db.scalars(
                select(Project).where(Project.user_id == user_id)
            ).all()
        }
        for index, pid in enumerate(ordered_ids):
            if pid in projects:
                projects[pid].sort_order = index
        self.db.commit()

    def max_sort_order(self, user_id: uuid.UUID) -> int:
        current = self.db.scalar(
            select(func.max(Project.sort_order)).where(Project.user_id == user_id)
        )
        return current if current is not None else -1

    def add_image(self, project: Project, url: str, alt_text: str | None) -> ProjectImage:
        image = ProjectImage(
            project_id=project.id,
            url=url,
            alt_text=alt_text,
            sort_order=len(project.images),
        )
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image

    def get_image(self, project_id: uuid.UUID, image_id: uuid.UUID) -> ProjectImage | None:
        return self.db.scalar(
            select(ProjectImage).where(
                ProjectImage.id == image_id, ProjectImage.project_id == project_id
            )
        )

    def delete_image(self, image: ProjectImage) -> None:
        self.db.delete(image)
        self.db.flush()
        self.renumber_images(image.project_id)
        self.db.commit()

    def renumber_images(self, project_id: uuid.UUID) -> None:
        """Make image sort_order a dense 0..n-1 sequence.

        Without this, deleting the first image leaves a gap and the next upload
        would reuse an order value that is already taken.
        """
        images = self.db.scalars(
            select(ProjectImage)
            .where(ProjectImage.project_id == project_id)
            .order_by(ProjectImage.sort_order, ProjectImage.id)
        ).all()
        for index, item in enumerate(images):
            item.sort_order = index
