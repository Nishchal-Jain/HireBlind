# HireBlind

Mini SaaS for **bias-free resume screening**.

**Clone:** `git clone https://github.com/Nishchal-Jain/HireBlind.git` — then install deps (see below); do not commit `node_modules` or `.venv`.

- **Frontend:** React (Vite) + Tailwind
- **Backend:** Python FastAPI
- **DB:** SQLite
- **Auth:** JWT (email/password) with roles `admin` and `recruiter`

## Features

- Auth: `/auth/signup`, `/auth/login`
- Recruiter: drag & drop multiple resume uploads (`.pdf`, `.docx`) with progress
- PII anonymisation (no original PII stored in DB) + **audit logs**
- Scoring: keyword match against admin job description → `score` + explanation tags
- Ranking dashboard: sorted by score, click to view anonymised resume
- Compliance panel: audit logs (PII removed) + why ranked (explanations) + confidence score
- Bonus:
  - Blind interview mode: `Reveal Identity` simulation logs an audit action
  - Bias override: recruiter can set `override_score` with a required reason

## Demo data

On first run (config: `HIREBLIND_SEED_DEMO=1`) the backend seeds:

- `admin@example.com` / `Admin123!`
- `recruiter@example.com` / `Recruit123!`
- a sample job description
- 3 sample resumes (embedded as text in code), stored only after anonymisation

## Run locally

### 1) Backend (FastAPI)

Prereqs:

- Python **3.12 recommended** (Python 3.14 can fail installs due to compiled dependencies / toolchains)

Commands:

```powershell
cd "C:\Users\Nirali jain\OneDrive\Desktop\HireBlind\hireblind\backend"
python -m pip install -r requirements.txt
uvicorn hireblind.backend.main:app --reload --port 8000
```

Backend runs at: `http://127.0.0.1:8000`

### 2) Frontend (React + Vite)

Commands:

```powershell
cd "C:\Users\Nirali jain\OneDrive\Desktop\HireBlind\hireblind\frontend"
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

### API base URL

Frontend calls the backend at `http://localhost:8000` by default (supports `VITE_API_URL`).

### One-command setup (recommended)

Run:

```powershell
cd "C:\Users\Nirali jain\OneDrive\Desktop\HireBlind\hireblind"
.\setup.ps1
```

## Notes on PDF extraction + spaCy

- PDF text extraction prefers **PyMuPDF** (`fitz`) if installed; otherwise it falls back to `pypdf` so local installs are easier.
- The PII anonymisation engine is implemented to use **spaCy NER when spaCy + `en_core_web_sm` are available**; otherwise it falls back to regex/heuristics so the app still runs.

Optional (for stricter spaCy compliance):

```powershell
pip install spacy
python -m spacy download en_core_web_sm
```

## How to use

1. Login as `admin@example.com`
2. Go to `/admin`, paste job description, click **Process Resumes**
3. Login as `recruiter@example.com`
4. Upload resumes on `/recruiter`
5. View ranking + compliance evidence on `/compliance`

## Key backend endpoints

- `POST /auth/signup`
- `POST /auth/login`
- `POST /upload`
- `POST /process-resumes` (admin only)
- `GET /get-candidates`
- `GET /get-audit-logs?candidate_id=...`
- `POST /update-ranking` (recruiter only)

