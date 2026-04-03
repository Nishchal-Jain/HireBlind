from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy.orm import Session

from hireblind.backend.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_removed_fields(self, candidate_id: int, removed_fields: Iterable[str]) -> None:
        # Store one audit row per removed field category (hackathon-friendly + easy to interpret).
        for field in removed_fields:
            self.db.add(
                AuditLog(
                    candidate_id=candidate_id,
                    removed_field=field,
                    timestamp=datetime.now(timezone.utc),
                    details=None,
                )
            )

    def log_action(self, candidate_id: int, removed_field: str, details: str | None) -> None:
        self.db.add(
            AuditLog(
                candidate_id=candidate_id,
                removed_field=removed_field,
                timestamp=datetime.now(timezone.utc),
                details=details,
            )
        )

