from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import User, MemoryProfile, Progress
from app.core.security import get_current_user
from app.services import ai as ai_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    language_code: str  # "hi", "de", "ja"


class ChatResponse(BaseModel):
    reply: str
    correction: str
    encouragement: str
    xp_awarded: int
    total_xp: int


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    if payload.language_code not in ("hi", "de", "ja"):
        raise HTTPException(status_code=422, detail="Unsupported language code")

    # Load memory profile
    profile = db.query(MemoryProfile).filter(MemoryProfile.user_id == current_user.id).first()
    if not profile:
        profile = MemoryProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    # Call AI
    result = ai_service.generate_tutor_response(
        message=payload.message,
        language_code=payload.language_code,
        memory_notes=profile.notes or "",
        vocab_focus=profile.vocab_focus or "",
        grammar_focus=profile.grammar_focus or "",
    )

    xp = result.get("xp_awarded", 10)

    # Update memory profile
    if result.get("vocab_update"):
        existing = profile.vocab_focus or ""
        profile.vocab_focus = (existing + "; " + result["vocab_update"]).strip("; ")
    if result.get("grammar_update"):
        existing = profile.grammar_focus or ""
        profile.grammar_focus = (existing + "; " + result["grammar_update"]).strip("; ")

    # Update XP and log progress
    current_user.xp += xp
    progress = Progress(
        user_id=current_user.id,
        language_code=payload.language_code,
        session_type="chat",
        xp_earned=xp,
    )
    db.add(progress)
    db.commit()
    db.refresh(current_user)

    return ChatResponse(
        reply=result.get("reply", ""),
        correction=result.get("correction", ""),
        encouragement=result.get("encouragement", ""),
        xp_awarded=xp,
        total_xp=current_user.xp,
    )
