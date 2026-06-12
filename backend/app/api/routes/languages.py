from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import User, UserLanguage, Progress
from app.core.security import get_current_user
from app.services import ai as ai_service

router = APIRouter(prefix="/languages", tags=["languages"])

SUPPORTED_LANGUAGES = [
    {"code": "hi", "name": "Hindi", "native": "हिन्दी", "flag": "🇮🇳"},
    {"code": "de", "name": "German", "native": "Deutsch", "flag": "🇩🇪"},
    {"code": "ja", "name": "Japanese", "native": "日本語", "flag": "🇯🇵"},
]

HINDI_ALPHABETS = [
    {"letter": "अ", "roman": "a", "example": "अनार (anaar) - pomegranate"},
    {"letter": "आ", "roman": "aa", "example": "आम (aam) - mango"},
    {"letter": "इ", "roman": "i", "example": "इमली (imli) - tamarind"},
    {"letter": "ई", "roman": "ee", "example": "ईख (eekh) - sugarcane"},
    {"letter": "उ", "roman": "u", "example": "उल्लू (ullu) - owl"},
    {"letter": "ऊ", "roman": "oo", "example": "ऊन (oon) - wool"},
    {"letter": "ए", "roman": "e", "example": "एड़ी (edhi) - heel"},
    {"letter": "ऐ", "roman": "ai", "example": "ऐनक (ainak) - glasses"},
    {"letter": "ओ", "roman": "o", "example": "ओखली (okhli) - mortar"},
    {"letter": "औ", "roman": "au", "example": "औरत (aurat) - woman"},
    {"letter": "क", "roman": "ka", "example": "कमल (kamal) - lotus"},
    {"letter": "ख", "roman": "kha", "example": "खरगोश (khargosh) - rabbit"},
    {"letter": "ग", "roman": "ga", "example": "गाय (gaay) - cow"},
    {"letter": "घ", "roman": "gha", "example": "घड़ी (ghadi) - watch"},
    {"letter": "च", "roman": "cha", "example": "चाँद (chaand) - moon"},
    {"letter": "छ", "roman": "chha", "example": "छतरी (chhatri) - umbrella"},
    {"letter": "ज", "roman": "ja", "example": "जहाज (jahaaz) - ship"},
    {"letter": "झ", "roman": "jha", "example": "झंडा (jhanda) - flag"},
    {"letter": "ट", "roman": "ta", "example": "टमाटर (tamatar) - tomato"},
    {"letter": "ड", "roman": "da", "example": "डमरू (damru) - drum"},
    {"letter": "त", "roman": "ta", "example": "तारा (taara) - star"},
    {"letter": "थ", "roman": "tha", "example": "थाली (thaali) - plate"},
    {"letter": "द", "roman": "da", "example": "दर्पण (darpan) - mirror"},
    {"letter": "न", "roman": "na", "example": "नाक (naak) - nose"},
    {"letter": "प", "roman": "pa", "example": "पानी (paani) - water"},
    {"letter": "फ", "roman": "pha", "example": "फूल (phool) - flower"},
    {"letter": "ब", "roman": "ba", "example": "बादल (baadal) - cloud"},
    {"letter": "भ", "roman": "bha", "example": "भालू (bhaalu) - bear"},
    {"letter": "म", "roman": "ma", "example": "मछली (machhli) - fish"},
    {"letter": "य", "roman": "ya", "example": "यात्रा (yaatra) - journey"},
    {"letter": "र", "roman": "ra", "example": "राजा (raaja) - king"},
    {"letter": "ल", "roman": "la", "example": "लड्डू (laddu) - sweet"},
    {"letter": "व", "roman": "va", "example": "वायु (vaayu) - air"},
    {"letter": "श", "roman": "sha", "example": "शेर (sher) - lion"},
    {"letter": "स", "roman": "sa", "example": "सूरज (suraj) - sun"},
    {"letter": "ह", "roman": "ha", "example": "हाथी (haathi) - elephant"},
]


class TranslateRequest(BaseModel):
    text: str
    target_language: str


class TranslateResponse(BaseModel):
    translated_text: str
    romanized_text: str
    notes: str


class EnrollRequest(BaseModel):
    language_code: str


@router.get("")
def get_languages():
    return SUPPORTED_LANGUAGES


@router.get("/hindi-alphabets")
def get_hindi_alphabets():
    return HINDI_ALPHABETS


@router.post("/translate", response_model=TranslateResponse)
def translate(
    payload: TranslateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.text.strip():
        raise HTTPException(status_code=422, detail="Text cannot be empty")

    result = ai_service.generate_translation(payload.text, payload.target_language)

    # Log progress
    progress = Progress(
        user_id=current_user.id,
        language_code=payload.target_language,
        session_type="translate",
        xp_earned=5,
    )
    current_user.xp += 5
    db.add(progress)
    db.commit()

    return TranslateResponse(
        translated_text=result.get("translated_text", ""),
        romanized_text=result.get("romanized_text", ""),
        notes=result.get("notes", ""),
    )


@router.post("/pronunciation")
async def analyze_pronunciation(
    audio: UploadFile = File(...),
    expected_text: str = Form(...),
    language_code: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    audio_bytes = await audio.read()
    transcript = ai_service.transcribe_audio(audio_bytes, audio.filename or "audio.webm")
    feedback = ai_service.analyze_pronunciation(transcript, expected_text, language_code)

    xp = 10
    progress = Progress(
        user_id=current_user.id,
        language_code=language_code,
        session_type="pronunciation",
        xp_earned=xp,
    )
    current_user.xp += xp
    db.add(progress)
    db.commit()

    return {**feedback, "transcript": transcript, "xp_awarded": xp}


@router.post("/enroll")
def enroll_language(
    payload: EnrollRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    supported = {l["code"]: l for l in SUPPORTED_LANGUAGES}
    if payload.language_code not in supported:
        raise HTTPException(status_code=422, detail="Unsupported language")

    existing = db.query(UserLanguage).filter(
        UserLanguage.user_id == current_user.id,
        UserLanguage.language_code == payload.language_code,
    ).first()

    if existing:
        existing.is_active = True
        db.commit()
        return {"message": "Already enrolled", "language": payload.language_code}

    lang_info = supported[payload.language_code]
    ul = UserLanguage(
        user_id=current_user.id,
        language_code=payload.language_code,
        language_name=lang_info["name"],
    )
    db.add(ul)
    db.commit()
    return {"message": "Enrolled successfully", "language": payload.language_code}


@router.get("/my-languages")
def get_my_languages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return current_user.languages


@router.get("/progress")
def get_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {
        "xp": current_user.xp,
        "streak": current_user.streak,
        "sessions": len(current_user.progress),
        "languages": [
            {
                "code": ul.language_code,
                "name": ul.language_name,
                "accuracy": ul.accuracy,
                "fluency": ul.fluency,
                "sessions": ul.sessions,
            }
            for ul in current_user.languages
        ],
    }
