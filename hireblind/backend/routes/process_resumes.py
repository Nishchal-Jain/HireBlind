from __future__ import annotations

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from hireblind.backend.models.candidate import Candidate
from hireblind.backend.models.user import User
from hireblind.backend.services.candidate_service import CandidateService
from hireblind.backend.utils.auth_deps import get_db_session, require_admin


router = APIRouter(prefix="", tags=["scoring"])


class ProcessResumesRequest(BaseModel):
    job_description: str


class ProcessResumesResponse(BaseModel):
    scored_candidates: int
    job_description_saved: bool = True


@router.post("/process-resumes", response_model=ProcessResumesResponse)
def process_resumes(
    payload: ProcessResumesRequest,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_admin()),
) -> ProcessResumesResponse:
    service = CandidateService(db)
    try:
        service.set_job_description(payload.job_description)
        service.score_all_candidates(payload.job_description)
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    count = db.query(Candidate).count()
    return ProcessResumesResponse(scored_candidates=count, job_description_saved=True)

