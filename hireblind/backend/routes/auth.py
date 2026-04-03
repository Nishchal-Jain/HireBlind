from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from hireblind.backend.models.user import User
from hireblind.backend.utils.auth_deps import get_db_session
from hireblind.backend.utils.security import create_access_token, hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=200)
    role: str = Field(description="admin | recruiter")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: EmailStr


@router.post("/signup", status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db_session)) -> dict:
    role = (payload.role or "").strip().lower()
    if role not in {"admin", "recruiter"}:
        raise HTTPException(status_code=400, detail="role must be admin or recruiter")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.commit()

    access_token = create_access_token(subject=str(user.id), role=user.role)
    model = AuthResponse(access_token=access_token, role=user.role, email=user.email)
    # Pydantic v1/v2 compatibility: prefer model_dump when available.
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db_session)) -> AuthResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(subject=str(user.id), role=user.role)
    return AuthResponse(access_token=access_token, role=user.role, email=user.email)

