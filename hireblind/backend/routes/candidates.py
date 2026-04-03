from __future__ import annotations

import json
from typing import Any, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from hireblind.backend.models.candidate import Candidate
from hireblind.backend.models.user import User
from hireblind.backend.services.candidate_service import CandidateService
from hireblind.backend.utils.auth_deps import get_db_session, require_roles


router = APIRouter(prefix="", tags=["candidates"])


class CandidateExplanation(BaseModel):
    score: int | None
    explanation: List[str]


class CandidateResponse(BaseModel):
    candidate_id: int
    anonymised_resume_text: str
    score: int | None
    final_score: int | None
    explanation: List[str]
    created_at: str


@router.get("/get-candidates", response_model=list[CandidateResponse])
def get_candidates(
    db: Session = Depends(get_db_session),
    _: User = Depends(require_roles("admin", "recruiter")),
) -> list[CandidateResponse]:
    service = CandidateService(db)
    candidates = service.get_candidates_sorted()

    out: list[CandidateResponse] = []
    for c in candidates:
        explanation: List[str] = []
        if c.explanation_json:
            try:
                explanation = json.loads(c.explanation_json)
            except Exception:
                explanation = []

        out.append(
            CandidateResponse(
                candidate_id=c.id,
                anonymised_resume_text=c.anonymised_resume_text,
                score=c.score,
                final_score=c.final_score,
                explanation=explanation,
                created_at=c.created_at.isoformat() if c.created_at else "",
            )
        )
    return out

