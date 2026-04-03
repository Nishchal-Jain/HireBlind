from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from hireblind.backend.models.candidate import Candidate
from hireblind.backend.models.user import User
from hireblind.backend.services.candidate_service import CandidateService
from hireblind.backend.services.scoring_service import parse_explanation_json
from hireblind.backend.utils.auth_deps import get_db_session, require_roles
from hireblind.backend.utils.timefmt import utc_iso


router = APIRouter(prefix="", tags=["candidates"])


class CandidateResponse(BaseModel):
    candidate_id: int
    upload_label: str | None = None
    anonymised_resume_text: str
    score: int | None
    final_score: int | None
    explanation: List[str]
    scoring_breakdown: dict[str, Any] | None = None
    is_override: bool = False
    override_score: int | None = None
    override_reason: str | None = None
    override_at: str | None = None
    created_at: str
    updated_at: str


@router.get("/get-candidates", response_model=list[CandidateResponse])
def get_candidates(
    db: Session = Depends(get_db_session),
    _: User = Depends(require_roles("admin", "recruiter")),
) -> list[CandidateResponse]:
    service = CandidateService(db)
    candidates = service.get_candidates_sorted()

    out: list[CandidateResponse] = []
    for c in candidates:
        explanation, breakdown = parse_explanation_json(c.explanation_json)
        out.append(
            CandidateResponse(
                candidate_id=c.id,
                upload_label=c.upload_label,
                anonymised_resume_text=c.anonymised_resume_text,
                score=c.score,
                final_score=c.final_score,
                explanation=explanation,
                scoring_breakdown=breakdown,
                is_override=c.override_score is not None,
                override_score=c.override_score,
                override_reason=c.override_reason,
                override_at=utc_iso(c.override_at) if c.override_at else None,
                created_at=utc_iso(c.created_at),
                updated_at=utc_iso(c.updated_at),
            )
        )
    return out


@router.delete("/candidates/{candidate_id}")
def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_roles("admin", "recruiter")),
) -> dict:
    row = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    db.delete(row)
    db.commit()
    return {"ok": True, "deleted_id": candidate_id}
