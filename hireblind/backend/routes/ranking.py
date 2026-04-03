from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from hireblind.backend.models.audit_log import AuditLog
from hireblind.backend.models.candidate import Candidate
from hireblind.backend.models.user import User
from hireblind.backend.services.audit_service import AuditService
from hireblind.backend.utils.auth_deps import get_db_session, require_recruiter


router = APIRouter(prefix="", tags=["ranking"])


class UpdateRankingRequest(BaseModel):
    candidate_id: int
    reason: str = Field(min_length=3, max_length=2000)
    # If provided, we treat this as a manual bias override and update final ranking.
    override_score: int | None = Field(default=None, ge=0, le=100)


@router.post("/update-ranking")
def update_ranking(
    payload: UpdateRankingRequest,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_recruiter()),
) -> dict:
    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    audit = AuditService(db)
    if payload.override_score is not None:
        candidate.override_score = payload.override_score
        candidate.final_score = payload.override_score
        audit.log_action(candidate.id, removed_field="manual_override", details=payload.reason)
    else:
        # Blind reveal simulation: log it, but don't change ranking/score.
        audit.log_action(candidate.id, removed_field="blind_reveal", details=payload.reason)

    db.commit()
    return {"ok": True}

