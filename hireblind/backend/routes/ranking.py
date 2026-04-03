from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from hireblind.backend.models.candidate import Candidate
from hireblind.backend.models.user import User
from hireblind.backend.services.audit_service import AuditService
from hireblind.backend.utils.auth_deps import get_db_session, require_recruiter
from hireblind.backend.utils.timefmt import utc_iso


router = APIRouter(prefix="", tags=["ranking"])


class UpdateRankingRequest(BaseModel):
    candidate_id: int
    reason: str = Field(min_length=3, max_length=2000)
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
    now = datetime.now(timezone.utc)

    if payload.override_score is not None:
        candidate.override_score = payload.override_score
        candidate.final_score = payload.override_score
        candidate.override_reason = payload.reason.strip()
        candidate.override_at = now
        details = json.dumps(
            {
                "action": "manual_override",
                "override_score": payload.override_score,
                "reason": payload.reason.strip(),
                "recorded_at": now.isoformat(),
            },
            ensure_ascii=False,
        )
        audit.log_action(candidate.id, removed_field="manual_override", details=details)
    else:
        details = json.dumps(
            {
                "action": "blind_reveal",
                "reason": payload.reason.strip(),
                "recorded_at": now.isoformat(),
            },
            ensure_ascii=False,
        )
        audit.log_action(candidate.id, removed_field="blind_reveal", details=details)

    candidate.updated_at = now
    db.commit()
    db.refresh(candidate)
    return {
        "ok": True,
        "override_at": utc_iso(candidate.override_at) if candidate.override_at else None,
        "override_score": candidate.override_score,
        "final_score": candidate.final_score,
    }
