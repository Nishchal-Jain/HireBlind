from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import DB_PATH

Base = declarative_base()


def _sqlite_url(path: Path) -> str:
    # Ensure we always use an absolute path (important on Windows).
    return f"sqlite:///{str(path.resolve())}"


engine = create_engine(
    _sqlite_url(DB_PATH),
    connect_args={"check_same_thread": False} if DB_PATH.suffix == ".db" else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    # Import models so SQLAlchemy registers them.
    from hireblind.backend.models.user import User  # noqa: F401
    from hireblind.backend.models.candidate import Candidate  # noqa: F401
    from hireblind.backend.models.audit_log import AuditLog  # noqa: F401
    from hireblind.backend.models.job_setting import JobSetting  # noqa: F401

    Base.metadata.create_all(bind=engine)

