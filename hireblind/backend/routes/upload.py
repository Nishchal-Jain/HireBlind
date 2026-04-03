from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from hireblind.backend.models.user import User
from hireblind.backend.services.resume_service import ResumeService
from hireblind.backend.utils.auth_deps import get_db_session, require_recruiter


router = APIRouter(prefix="", tags=["resumes"])


class UploadResponse(BaseModel):
    candidate_ids: list[int]


@router.post("/upload", response_model=UploadResponse)
def upload_resumes(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_recruiter()),
) -> UploadResponse:
    try:
        service = ResumeService(db)
        candidate_ids = service.process_upload(files)
        return UploadResponse(candidate_ids=candidate_ids)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

