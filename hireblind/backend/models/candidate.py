from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hireblind.backend.utils.db import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anonymised_resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Original filename only (helps recruiters map uploads; resume PII is not stored).
    upload_label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Scoring fields
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # computed score
    explanation_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: tags + breakdown
    final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # score or recruiter override
    override_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    audit_logs = relationship("AuditLog", back_populates="candidate", cascade="all, delete-orphan")

