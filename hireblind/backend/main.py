from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hireblind.backend.routes.auth import router as auth_router
from hireblind.backend.routes.upload import router as upload_router
from hireblind.backend.routes.process_resumes import router as process_resumes_router
from hireblind.backend.routes.candidates import router as candidates_router
from hireblind.backend.routes.audit_logs import router as audit_logs_router
from hireblind.backend.routes.ranking import router as ranking_router
from hireblind.backend.utils.config import FRONTEND_ORIGINS, SEED_DEMO
from hireblind.backend.utils.db import init_db
from hireblind.backend.services.seed_service import seed_if_needed


def create_app() -> FastAPI:
    app = FastAPI(title="HireBlind", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=FRONTEND_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(upload_router)
    app.include_router(process_resumes_router)
    app.include_router(candidates_router)
    app.include_router(audit_logs_router)
    app.include_router(ranking_router)

    return app


app = create_app()


@app.on_event("startup")
def _startup() -> None:
    init_db()
    if SEED_DEMO:
        seed_if_needed()
    else:
        print("No seeding needed")

