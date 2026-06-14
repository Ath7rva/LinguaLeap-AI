import hashlib
import hmac
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token, generate_opaque_token, get_current_user, hash_password, token_hash, verify_password,
)
from app.core.config import get_settings
from app.database import get_db
from app.models import AuditLog, MemoryProfile, OneTimeToken, RefreshSession, ResearcherInvitation, User
from app.services.rate_limit import enforce_rate_limit
from app.services.email import send_transactional_email

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
    invitation_token: str = ""
    selected_language: str = "hi"


class TokenRequest(BaseModel):
    token: str


class EmailRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def email_delivery_available():
    return settings.email_delivery_mode == "resend" and bool(settings.resend_api_key)


def email_verification_required():
    return email_delivery_available() or (
        settings.email_delivery_mode == "console" and settings.environment != "production"
    )


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
        "email_verified": user.email_verified,
        "proficiency": user.proficiency,
        "cefr_level": user.cefr_level,
        "placement_score": user.placement_score,
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


def _request_identity(request: Request):
    forwarded = request.headers.get("x-forwarded-for", "")
    return (
        request.headers.get("user-agent", "")[:500],
        (forwarded.split(",")[0].strip() or (request.client.host if request.client else ""))[:120],
    )


def create_refresh_session(db: Session, user: User, request: Request):
    raw = generate_opaque_token()
    user_agent, ip = _request_identity(request)
    db.add(RefreshSession(
        id=uuid4().hex,
        user_id=user.id,
        token_hash=token_hash(raw),
        user_agent=user_agent,
        ip_address=ip,
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
    ))
    return raw


def token_response(db: Session, user: User, request: Request, rotate_from: RefreshSession | None = None):
    if rotate_from:
        rotate_from.revoked_at = datetime.utcnow()
    refresh_token = create_refresh_session(db, user, request)
    db.commit()
    return {
        "access_token": create_access_token({"sub": str(user.id), "ver": user.token_version}),
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    enforce_rate_limit(request, "auth-register", limit=8)
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    if "@" not in payload.email or payload.email.startswith("@") or payload.email.endswith("@"):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    email = payload.email.lower().strip()
    if payload.selected_language not in {"hi", "de", "ja"}:
        raise HTTPException(status_code=422, detail="Unsupported language")
    experiment_group, delivery_group = experiment_assignment(email, payload.research_consent)
    wants_researcher = email.endswith("@admin.local") or bool(payload.invitation_token)
    invitation = None
    if payload.invitation_token:
        invitation = db.query(ResearcherInvitation).filter(
            ResearcherInvitation.token_hash == token_hash(payload.invitation_token),
            ResearcherInvitation.accepted_at.is_(None),
            ResearcherInvitation.expires_at > datetime.utcnow(),
        ).first()
        if not invitation or invitation.email.lower() != email:
            raise HTTPException(status_code=403, detail="Researcher invitation is invalid or expired")
    elif wants_researcher and (
        not settings.researcher_access_code
        or not hmac.compare_digest(payload.researcher_access_code, settings.researcher_access_code)
    ):
        raise HTTPException(status_code=403, detail="A valid researcher invitation is required")

    user = User(
        anonymous_id=f"LL-{uuid4().hex[:12].upper()}",
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role="researcher" if wants_researcher else "learner",
        email_verified=bool(invitation) or not email_verification_required(),
        proficiency=payload.proficiency,
        cefr_level={"beginner": "A1", "intermediate": "A2", "advanced": "B1"}.get(payload.proficiency, "A1"),
        learning_goal=payload.learning_goal,
        selected_language=payload.selected_language,
        experiment_group=experiment_group,
        delivery_group=delivery_group,
        research_consent=payload.research_consent,
        consented_at=datetime.utcnow() if payload.research_consent else None,
        pre_test_score=payload.pre_test_score,
    )
    db.add(user)
    db.flush()
    if invitation:
        invitation.accepted_at = datetime.utcnow()
    db.add(MemoryProfile(user_id=user.id))
    verify_token = ""
    if not user.email_verified:
        verify_token = generate_opaque_token()
        db.add(OneTimeToken(
            user_id=user.id,
            purpose="verify-email",
            token_hash=token_hash(verify_token),
            expires_at=datetime.utcnow() + timedelta(hours=24),
        ))
    db.add(AuditLog(user_id=user.id, action="account.registered", resource_type="user", resource_id=str(user.id)))
    db.commit()
    db.refresh(user)
    if verify_token:
        send_transactional_email(
            user.email,
            "Verify your LinguaLeap AI email",
            f'<p>Verify your email to protect your learning account.</p><p><code>{verify_token}</code></p>',
        )
    response = token_response(db, user, request)
    response["email_delivery_available"] = email_delivery_available()
    if verify_token and settings.email_delivery_mode == "console" and settings.environment != "production":
        response["verification_token"] = verify_token
    return response


@router.post("/login")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    enforce_rate_limit(request, "auth-login", limit=12)
    user = db.query(User).filter(User.email == form_data.username.lower().strip()).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    db.add(AuditLog(user_id=user.id, action="session.login", resource_type="user", resource_id=str(user.id)))
    return token_response(db, user, request)


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)


@router.post("/refresh")
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    session = db.query(RefreshSession).filter(
        RefreshSession.token_hash == token_hash(payload.refresh_token),
        RefreshSession.revoked_at.is_(None),
        RefreshSession.expires_at > datetime.utcnow(),
    ).first()
    if not session:
        raise HTTPException(status_code=401, detail="Refresh session is invalid or expired")
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Session user no longer exists")
    return token_response(db, user, request, rotate_from=session)


@router.post("/logout", status_code=204)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    session = db.query(RefreshSession).filter(RefreshSession.token_hash == token_hash(payload.refresh_token)).first()
    if session and not session.revoked_at:
        session.revoked_at = datetime.utcnow()
        db.commit()


@router.post("/logout-all", status_code=204)
def logout_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user.token_version += 1
    db.query(RefreshSession).filter(
        RefreshSession.user_id == user.id,
        RefreshSession.revoked_at.is_(None),
    ).update({RefreshSession.revoked_at: datetime.utcnow()})
    db.commit()


@router.get("/sessions")
def sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [{
        "id": row.id,
        "user_agent": row.user_agent,
        "ip_address": row.ip_address,
        "created_at": row.created_at,
        "expires_at": row.expires_at,
        "active": row.revoked_at is None and row.expires_at > datetime.utcnow(),
    } for row in db.query(RefreshSession).filter(RefreshSession.user_id == user.id).order_by(RefreshSession.created_at.desc()).all()]


@router.post("/verify-email")
def verify_email(payload: TokenRequest, db: Session = Depends(get_db)):
    row = db.query(OneTimeToken).filter(
        OneTimeToken.purpose == "verify-email",
        OneTimeToken.token_hash == token_hash(payload.token),
        OneTimeToken.used_at.is_(None),
        OneTimeToken.expires_at > datetime.utcnow(),
    ).first()
    if not row:
        raise HTTPException(status_code=422, detail="Verification token is invalid or expired")
    user = db.query(User).filter(User.id == row.user_id).first()
    user.email_verified = True
    row.used_at = datetime.utcnow()
    db.commit()
    return {"verified": True}


@router.post("/resend-verification")
def resend_verification(payload: EmailRequest, request: Request, db: Session = Depends(get_db)):
    enforce_rate_limit(request, "auth-verify", limit=5)
    if not email_delivery_available():
        raise HTTPException(status_code=503, detail="Email delivery is not configured for this deployment")
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or user.email_verified:
        return {"message": "If verification is required, a new email has been sent."}
    db.query(OneTimeToken).filter(
        OneTimeToken.user_id == user.id,
        OneTimeToken.purpose == "verify-email",
        OneTimeToken.used_at.is_(None),
    ).update({OneTimeToken.used_at: datetime.utcnow()})
    raw = generate_opaque_token()
    db.add(OneTimeToken(
        user_id=user.id,
        purpose="verify-email",
        token_hash=token_hash(raw),
        expires_at=datetime.utcnow() + timedelta(hours=24),
    ))
    db.commit()
    send_transactional_email(
        user.email,
        "Verify your LinguaLeap AI email",
        f'<p>Verify your email to protect your learning account.</p><p><code>{raw}</code></p>',
    )
    return {"message": "If verification is required, a new email has been sent."}


@router.post("/forgot-password")
def forgot_password(payload: EmailRequest, request: Request, db: Session = Depends(get_db)):
    enforce_rate_limit(request, "auth-reset", limit=5)
    if not email_delivery_available() and settings.environment == "production":
        raise HTTPException(
            status_code=503,
            detail="Password recovery email is temporarily unavailable. Contact the site administrator.",
        )
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    response = {"message": "If that account exists, a reset link has been issued."}
    if user:
        raw = generate_opaque_token()
        db.add(OneTimeToken(
            user_id=user.id,
            purpose="reset-password",
            token_hash=token_hash(raw),
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        ))
        db.commit()
        send_transactional_email(
            user.email,
            "Reset your LinguaLeap AI password",
            f'<p>This token expires in 30 minutes.</p><p><code>{raw}</code></p>',
        )
        if settings.email_delivery_mode == "console" and settings.environment != "production":
            response["reset_token"] = raw
    return response


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(payload.password) < 10:
        raise HTTPException(status_code=422, detail="Password must be at least 10 characters")
    row = db.query(OneTimeToken).filter(
        OneTimeToken.purpose == "reset-password",
        OneTimeToken.token_hash == token_hash(payload.token),
        OneTimeToken.used_at.is_(None),
        OneTimeToken.expires_at > datetime.utcnow(),
    ).first()
    if not row:
        raise HTTPException(status_code=422, detail="Reset token is invalid or expired")
    user = db.query(User).filter(User.id == row.user_id).first()
    user.password_hash = hash_password(payload.password)
    user.token_version += 1
    row.used_at = datetime.utcnow()
    db.query(RefreshSession).filter(RefreshSession.user_id == user.id).update({RefreshSession.revoked_at: datetime.utcnow()})
    db.commit()
    return {"reset": True}
