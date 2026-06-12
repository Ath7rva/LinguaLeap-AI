import hashlib
import hmac
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.core.config import get_settings
from app.database import get_db
from app.models import MemoryProfile, User

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    proficiency: str = "beginner"
    learning_goal: str = "Everyday conversation"
    research_consent: bool = False
    pre_test_score: float | None = None
    researcher_access_code: str = ""


def experiment_assignment(email: str, consent: bool):
    if not consent:
        return "not_enrolled", "not_enrolled"
    digest = hmac.new(
        settings.secret_key.encode("utf-8"),
        email.lower().strip().encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    bucket = int(digest[:8], 16)
    return (
        "llm_tutor" if bucket % 2 == 0 else "structured_baseline",
        "text_only" if (bucket // 2) % 2 == 0 else "multimodal",
    )


def serialize_user(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "proficiency": user.proficiency,
        "learning_goal": user.learning_goal,
        "selected_language": user.selected_language,
        "anonymous_id": user.anonymous_id,
        "experiment_group": user.experiment_group,
        "delivery_group": user.delivery_group,
        "research_consent": user.research_consent,
        "pre_test_score": user.pre_test_score,
        "post_test_score": user.post_test_score,
        "xp": user.xp,
        "streak": user.streak,
    }


def token_response(user: User):
    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    if "@" not in payload.email or payload.email.startswith("@") or payload.email.endswith("@"):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    email = payload.email.lower().strip()
    experiment_group, delivery_group = experiment_assignment(email, payload.research_consent)
    wants_researcher = email.endswith("@admin.local")
    if wants_researcher and (
        not settings.researcher_access_code
        or not hmac.compare_digest(payload.researcher_access_code, settings.researcher_access_code)
    ):
        raise HTTPException(status_code=403, detail="A valid researcher access code is required")

    user = User(
        anonymous_id=f"LL-{uuid4().hex[:12].upper()}",
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role="researcher" if wants_researcher else "learner",
        proficiency=payload.proficiency,
        learning_goal=payload.learning_goal,
        experiment_group=experiment_group,
        delivery_group=delivery_group,
        research_consent=payload.research_consent,
        consented_at=datetime.utcnow() if payload.research_consent else None,
        pre_test_score=payload.pre_test_score,
    )
    db.add(user)
    db.flush()
    db.add(MemoryProfile(user_id=user.id))
    db.commit()
    db.refresh(user)
    return token_response(user)


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username.lower().strip()).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_response(user)


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)
