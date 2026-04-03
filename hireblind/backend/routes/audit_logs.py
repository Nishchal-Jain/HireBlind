from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from hireblind.backend.models.audit_log import AuditLog
from hireblind.backend.models.user import User
from hireblind.backend.services.candidate_service import CandidateService
from hireblind.backend.utils.auth_deps import get_db_session, require_roles


router = APIRouter(prefix="", tags=["audit"])


class AuditLogResponse(BaseModel):
    id: int
    candidate_id: int
    removed_field: str
    timestamp: str
    details: str | None = None


@router.get("/get-audit-logs", response_model=list[AuditLogResponse])
def get_audit_logs(
    candidate_id: int | None = Query(default=None),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_roles("admin", "recruiter")),
) -> List[AuditLogResponse]:
    service = CandidateService(db)
    logs = service.get_audit_logs(candidate_id=candidate_id)
    return [
        AuditLogResponse(
            id=l.id,
            candidate_id=l.candidate_id,
            removed_field=l.removed_field,
            timestamp=l.timestamp.isoformat() if l.timestamp else "",
            details=l.details,
        )
        for l in logs
    ]

