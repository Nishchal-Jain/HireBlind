from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from hireblind.backend.utils.db import Base


class JobSetting(Base):
    __tablename__ = "job_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

