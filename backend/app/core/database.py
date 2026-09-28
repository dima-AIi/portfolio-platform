from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

_is_memory_sqlite = settings.DATABASE_URL == "sqlite:///:memory:"

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
pool_kwargs = {"poolclass": StaticPool} if _is_memory_sqlite else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, **pool_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
