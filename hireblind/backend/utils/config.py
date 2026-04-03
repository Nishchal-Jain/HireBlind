from __future__ import annotations

import os
from pathlib import Path


# Keep config centralized so routes/services stay clean.
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # hireblind/
DB_PATH = Path(os.environ.get("HIREBLIND_DB_PATH", str(PROJECT_ROOT / "hireblind.db")))

JWT_SECRET = os.environ.get("HIREBLIND_JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = os.environ.get("HIREBLIND_JWT_ALGORITHM", "HS256")
# Longer default avoids "Invalid token" / ExpiredSignature during normal demo use (override via env).
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("HIREBLIND_ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

# Upload limits (hackathon-friendly defaults).
MAX_FILES_PER_UPLOAD = int(os.environ.get("HIREBLIND_MAX_FILES_PER_UPLOAD", "10"))
MAX_FILE_SIZE_BYTES = int(os.environ.get("HIREBLIND_MAX_FILE_SIZE_BYTES", str(5 * 1024 * 1024)))  # 5MB
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# Demo seeding (on by default for local runs).
SEED_DEMO = os.environ.get("HIREBLIND_SEED_DEMO", "1") == "1"

# CORS origins for local dev.
FRONTEND_ORIGINS = [
    os.environ.get("HIREBLIND_FRONTEND_ORIGIN", "http://localhost:5173"),
    os.environ.get("HIREBLIND_FRONTEND_ORIGIN_2", "http://127.0.0.1:5173"),
]

