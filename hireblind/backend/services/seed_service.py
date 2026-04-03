from __future__ import annotations

from sqlalchemy.orm import Session

from hireblind.backend.models.candidate import Candidate
from hireblind.backend.models.job_setting import JobSetting
from hireblind.backend.models.user import User
from hireblind.backend.services.candidate_service import CandidateService
from hireblind.backend.services.resume_service import ResumeService
from hireblind.backend.utils.config import SEED_DEMO
from hireblind.backend.utils.db import SessionLocal
from hireblind.backend.utils.security import hash_password


SAMPLE_JOB_DESCRIPTION = """
We are looking for a Python/React engineer to build bias-free resume screening tools.
Required: 3+ years experience with Python, SQL, and REST APIs.
Preferred: React, machine learning basics, and data privacy compliance.
Responsibilities: extract and process resume text, score candidate matches, and build dashboards.
"""


SAMPLE_RESUMES: list[str] = [
    """
John Doe
john.doe@example.com
+1 (555) 123-4567
San Francisco, CA
Senior Software Engineer
I have 5 years of experience building REST APIs with Python and SQL.
Worked with React for front-end dashboards.
Graduated from Stanford University with a focus on data privacy.
He/him
""",
    """
Maria Gomez
gomez.maria@example.com
555-987-6543
New York, NY
Software Developer
3 years experience developing backend services in Python.
Built integrations using REST APIs and SQL queries.
Experience with React components for internal tools.
Studied at Harvard University.
She/her
""",
    """
Ahmed Khan
ahmed.khan@example.com
+44 20 7946 0958
London, UK
Full Stack Engineer
I have 4 years of experience with Python, React, and modern web stacks.
Designed data processing pipelines and scoring logic.
University of Cambridge Institute participant.
He/him
""",
]


def _seed_users(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    admin = User(
        email="admin@example.com",
        password_hash=hash_password("Admin123!"),
        role="admin",
    )
    recruiter = User(
        email="recruiter@example.com",
        password_hash=hash_password("Recruit123!"),
        role="recruiter",
    )
    db.add(admin)
    db.add(recruiter)
    db.commit()


def _seed_candidates_and_scores(db: Session) -> None:
    # Only seed resumes if there are no candidates yet.
    if db.query(Candidate).count() == 0:
        try:
            resume_service = ResumeService(db)
            for i, resume_text in enumerate(SAMPLE_RESUMES):
                resume_service.create_candidate_from_text(resume_text, upload_label=f"sample_resume_{i + 1}.pdf")
            db.commit()
        except Exception:
            # Keep server booting even if spaCy model download isn't done yet.
            # Users can still upload real files after installing the model.
            return

    # Always ensure job description exists and candidates are scored.
    candidate_service = CandidateService(db)
    candidate_service.set_job_description(SAMPLE_JOB_DESCRIPTION)
    candidate_service.score_all_candidates(SAMPLE_JOB_DESCRIPTION)
    db.commit()


def seed_if_needed() -> None:
    if not SEED_DEMO:
        return

    db = SessionLocal()
    try:
        _seed_users(db)
        # Job settings can exist without candidates; handle both.
        if db.query(JobSetting).count() == 0 or db.query(Candidate).count() > 0:
            _seed_candidates_and_scores(db)
    finally:
        db.close()

