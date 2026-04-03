from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from hireblind.backend.models.audit_log import AuditLog
from hireblind.backend.models.candidate import Candidate
from hireblind.backend.models.job_setting import JobSetting
from hireblind.backend.services.scoring_service import score_resume


class CandidateService:
    def __init__(self, db: Session):
        self.db = db

    def set_job_description(self, job_description: str) -> None:
        job_description = (job_description or "").strip()
        if not job_description:
            raise ValueError("Job description cannot be empty")

        row = self.db.query(JobSetting).order_by(JobSetting.id.asc()).first()
        if not row:
            row = JobSetting(job_description=job_description)
            self.db.add(row)
        else:
            row.job_description = job_description
            row.updated_at = datetime.now(timezone.utc)

    def get_job_description(self) -> Optional[str]:
        row = self.db.query(JobSetting).order_by(JobSetting.id.asc()).first()
        return row.job_description if row else None

    def score_all_candidates(self, job_description: str) -> None:
        job_description = (job_description or "").strip()
        if not job_description:
            raise ValueError("Job description cannot be empty")

        now = datetime.now(timezone.utc)
        candidates: List[Candidate] = self.db.query(Candidate).order_by(Candidate.id.asc()).all()
        for c in candidates:
            confidence, explanation = score_resume(job_description, c.anonymised_resume_text)
            c.score = confidence
            c.explanation_json = json.dumps(explanation)
            c.updated_at = now
            # Preserve manual overrides if recruiter changed ranking.
            if c.override_score is None:
                c.final_score = confidence

    def get_candidates_sorted(self) -> List[Candidate]:
        # final_score can be NULL before admin processes resumes.
        # Place NULLs at the bottom.
        return (
            self.db.query(Candidate)
            .order_by((Candidate.final_score.is_(None)).asc(), Candidate.final_score.desc())
            .all()
        )

    def get_audit_logs(self, candidate_id: int | None = None) -> List[AuditLog]:
        q = self.db.query(AuditLog)
        if candidate_id is not None:
            q = q.filter(AuditLog.candidate_id == candidate_id)
        return q.order_by(AuditLog.timestamp.desc()).all()

