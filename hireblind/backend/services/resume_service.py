from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from hireblind.backend.models.candidate import Candidate
from hireblind.backend.services.anonymisation_service import AnonymisationService
from hireblind.backend.services.audit_service import AuditService
from hireblind.backend.utils.config import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MAX_FILES_PER_UPLOAD,
)
from hireblind.backend.utils.text_extraction import extract_text_from_docx, extract_text_from_pdf


def _candidate_letter(candidate_id: int) -> str:
    letters = ["A", "B", "C"]
    # candidate_id starts at 1
    return letters[(candidate_id - 1) % len(letters)]


class ResumeService:
    def __init__(self, db: Session):
        self.db = db
        self.anonymiser = AnonymisationService()
        self.audit = AuditService(db)

    def _validate_files(self, files: List[UploadFile]) -> None:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        if len(files) > MAX_FILES_PER_UPLOAD:
            raise HTTPException(status_code=400, detail=f"Max {MAX_FILES_PER_UPLOAD} files per upload")

    def _get_extension(self, upload_file: UploadFile) -> str:
        name = upload_file.filename or ""
        ext = Path(name).suffix.lower()
        return ext

    def create_candidate_from_text(self, resume_text: str) -> int:
        # Create the candidate row first so we have a stable candidate_id.
        # This ensures we never need to store any original PII in the DB.
        candidate = Candidate(anonymised_resume_text="")
        self.db.add(candidate)
        self.db.flush()  # Assigns candidate.id

        letter = _candidate_letter(candidate.id)
        anonymised, removed_fields = self.anonymiser.anonymize(resume_text, letter)
        if not anonymised.strip():
            anonymised = ""  # keep schema valid; scoring will likely be 0

        candidate.anonymised_resume_text = anonymised
        self.audit.log_removed_fields(candidate.id, removed_fields)
        return candidate.id

    def process_upload(self, files: List[UploadFile]) -> List[int]:
        self._validate_files(files)

        candidate_ids: list[int] = []
        for upload in files:
            ext = self._get_extension(upload)
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

            file_bytes = upload.file.read()
            if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large ({len(file_bytes)} bytes). Max is {MAX_FILE_SIZE_BYTES} bytes.",
                )

            if ext == ".pdf":
                resume_text = extract_text_from_pdf(file_bytes)
            else:
                resume_text = extract_text_from_docx(file_bytes)

            if not resume_text.strip():
                raise HTTPException(status_code=400, detail=f"Could not extract text from {upload.filename}")

            candidate_ids.append(self.create_candidate_from_text(resume_text))

        self.db.commit()
        return candidate_ids

