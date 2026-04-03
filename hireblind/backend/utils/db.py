from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
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


def _sqlite_add_column_if_missing(engine: Engine, table: str, column: str, ddl_type: str) -> None:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns(table)}
    if column in cols:
        return
    with engine.begin() as conn:
        conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {column} {ddl_type}'))


def _migrate_sqlite(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return
    _sqlite_add_column_if_missing(engine, "candidates", "upload_label", "VARCHAR(255)")
    _sqlite_add_column_if_missing(engine, "candidates", "override_reason", "TEXT")
    _sqlite_add_column_if_missing(engine, "candidates", "override_at", "DATETIME")
    _sqlite_add_column_if_missing(engine, "candidates", "updated_at", "DATETIME")
    if engine.dialect.name == "sqlite":
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE candidates SET updated_at = created_at WHERE updated_at IS NULL")
            )


def init_db() -> None:
    # Import models so SQLAlchemy registers them.
    from hireblind.backend.models.user import User  # noqa: F401
    from hireblind.backend.models.candidate import Candidate  # noqa: F401
    from hireblind.backend.models.audit_log import AuditLog  # noqa: F401
    from hireblind.backend.models.job_setting import JobSetting  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite(engine)

