import hashlib
import hmac
import math
import base64
from datetime import datetime, timedelta
from statistics import mean, pstdev
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import generate_opaque_token, get_current_user, token_hash
from app.database import SessionLocal, get_db
from app.models import (
    AIJob, AuditLog, Experiment, ExperimentEnrollment, GeneratedExercise, Interaction,
    ListeningAttempt, ProviderUsage, ResearcherInvitation, ReviewItem, SkillMastery, User,
)
from app.services import ai as ai_service
from app.services.adaptive import cefr_from_placement, learning_health, mastery_snapshot, recommendation, update_mastery
from app.services.rate_limit import enforce_rate_limit
from app.services.email import send_transactional_email
from app.services.pronunciation import compare_words

router = APIRouter(prefix="/advanced", tags=["advanced"])
settings = get_settings()

LISTENING_EXERCISES = {
    "hi": [
        {"id": "hi-listen-a1", "cefr": "A1", "audio_url": "/audio/hi-listen-a1.mp3", "text": "नमस्ते, आप कैसे हैं?", "romanization": "namaste, aap kaise hain?", "question": "What is the speaker asking?", "options": ["How are you?", "Where are you?", "What is your name?"], "answer": "How are you?"},
        {"id": "hi-listen-a2", "cefr": "A2", "audio_url": "/audio/hi-listen-a2.mp3", "text": "कृपया मुझे एक गिलास पानी दीजिए।", "romanization": "kripaya mujhe ek gilaas paani dijiye", "question": "What does the speaker request?", "options": ["A glass of water", "A train ticket", "A book"], "answer": "A glass of water"},
    ],
    "de": [
        {"id": "de-listen-a1", "cefr": "A1", "audio_url": "/audio/de-listen-a1.mp3", "text": "Guten Morgen. Wie geht es dir?", "romanization": "", "question": "What is the speaker asking?", "options": ["How are you?", "Where is the station?", "What time is it?"], "answer": "How are you?"},
        {"id": "de-listen-a2", "cefr": "A2", "audio_url": "/audio/de-listen-a2.mp3", "text": "Ich möchte eine Fahrkarte nach Berlin.", "romanization": "", "question": "What does the speaker want?", "options": ["A ticket to Berlin", "A coffee", "A hotel room"], "answer": "A ticket to Berlin"},
    ],
    "ja": [
        {"id": "ja-listen-a1", "cefr": "A1", "audio_url": "/audio/ja-listen-a1.mp3", "text": "おはようございます。お元気ですか。", "romanization": "ohayou gozaimasu. ogenki desu ka", "question": "What is the speaker asking?", "options": ["Are you well?", "Are you hungry?", "Are you a student?"], "answer": "Are you well?"},
        {"id": "ja-listen-a2", "cefr": "A2", "audio_url": "/audio/ja-listen-a2.mp3", "text": "駅までどうやって行きますか。", "romanization": "eki made dou yatte ikimasu ka", "question": "What is the speaker asking about?", "options": ["How to get to the station", "When the shop closes", "What food costs"], "answer": "How to get to the station"},
    ],
}

PLACEMENT_QUESTIONS = [
    {"id": "meaning", "skill": "vocabulary", "answer": "hello"},
    {"id": "order", "skill": "grammar", "answer": "correct"},
    {"id": "listen", "skill": "listening", "answer": "understood"},
    {"id": "write", "skill": "writing", "answer": "complete"},
]


class PlacementSubmission(BaseModel):
    answers: dict[str, str]


class ListeningSubmission(BaseModel):
    exercise_id: str
    answer: str
    playback_count: int = Field(default=1, ge=1, le=20)
    transcript_revealed: bool = False


class PracticeJobRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=120)


class GeneratedExerciseSubmission(BaseModel):
    answer: str = Field(max_length=500)
    engagement_seconds: int = Field(default=30, ge=1, le=3600)


class InvitationRequest(BaseModel):
    email: str
    expires_hours: int = Field(default=72, ge=1, le=720)


class ExperimentRequest(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    hypothesis: str = Field(default="", max_length=2000)
    version: str = Field(default="1.0", max_length=30)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    configuration: dict = Field(default_factory=lambda: {
        "tutor_groups": ["llm_tutor", "structured_baseline"],
        "delivery_groups": ["text_only", "multimodal"],
    })


def require_researcher(user: User):
    if user.role != "researcher":
        raise HTTPException(status_code=403, detail="Researcher role required")


def record_usage(db: Session, user_id: int, operation: str, usage: dict | None, success: bool = True):
    usage = usage or {}
    prompt = int(usage.get("prompt_tokens", 0))
    completion = int(usage.get("completion_tokens", 0))
    cost = (
        prompt / 1_000_000 * settings.groq_input_cost_per_million
        + completion / 1_000_000 * settings.groq_output_cost_per_million
    )
    db.add(ProviderUsage(
        user_id=user_id, provider="groq", operation=operation, model=ai_service.CHAT_MODEL,
        prompt_tokens=prompt, completion_tokens=completion, estimated_cost_usd=round(cost, 8),
        latency_ms=int(usage.get("latency_ms", 0)), success=success,
    ))


@router.get("/placement")
def placement_questions():
    return {
        "questions": [
            {"id": "meaning", "skill": "vocabulary", "prompt": "Can you identify a basic greeting?", "options": ["hello", "later", "unknown"]},
            {"id": "order", "skill": "grammar", "prompt": "Can you recognize a correct beginner sentence pattern?", "options": ["correct", "unsure"]},
            {"id": "listen", "skill": "listening", "prompt": "After hearing a short greeting, how much did you understand?", "options": ["understood", "partly", "not-yet"]},
            {"id": "write", "skill": "writing", "prompt": "Can you write one complete introductory sentence?", "options": ["complete", "partial", "not-yet"]},
        ],
        "note": "This is a product placement check, not an accredited CEFR examination.",
    }


@router.post("/placement")
def submit_placement(payload: PlacementSubmission, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    correct = sum(1 for item in PLACEMENT_QUESTIONS if payload.answers.get(item["id"], "").casefold() == item["answer"])
    score = round(correct / len(PLACEMENT_QUESTIONS) * 100)
    user.placement_score = score
    user.cefr_level = cefr_from_placement(score)
    user.proficiency = {"A1": "beginner", "A2": "intermediate", "B1": "advanced"}[user.cefr_level]
    for item in PLACEMENT_QUESTIONS:
        item_score = 100 if payload.answers.get(item["id"], "").casefold() == item["answer"] else 20
        update_mastery(db, user, user.selected_language, item["skill"], item_score)
    db.add(AuditLog(user_id=user.id, action="placement.completed", resource_type="user", resource_id=str(user.id), metadata_json={"score": score, "cefr": user.cefr_level}))
    db.commit()
    return {"score": score, "cefr_level": user.cefr_level, "recommendation": recommendation(db, user)}


@router.get("/learning-path")
def learning_path(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return learning_health(db, user)


@router.get("/listening")
def listening(user: User = Depends(get_current_user)):
    allowed = {"A1": {"A1"}, "A2": {"A1", "A2"}, "B1": {"A1", "A2", "B1"}}[user.cefr_level]
    return {"exercises": [item for item in LISTENING_EXERCISES[user.selected_language] if item["cefr"] in allowed]}


@router.post("/listening")
def submit_listening(payload: ListeningSubmission, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    exercise = next((item for rows in LISTENING_EXERCISES.values() for item in rows if item["id"] == payload.exercise_id), None)
    if not exercise:
        raise HTTPException(status_code=404, detail="Listening exercise not found")
    correct = payload.answer.strip().casefold() == exercise["answer"].casefold()
    score = max(0, (100 if correct else 25) - max(0, payload.playback_count - 2) * 5 - (15 if payload.transcript_revealed else 0))
    db.add(ListeningAttempt(
        user_id=user.id, exercise_id=payload.exercise_id, language_code=user.selected_language,
        answer=payload.answer, correct=correct, score=score, playback_count=payload.playback_count,
        transcript_revealed=payload.transcript_revealed,
    ))
    db.add(Interaction(
        user_id=user.id, language_code=user.selected_language, interaction_type="listening",
        skill="listening", proficiency_snapshot=user.proficiency, task_complexity=exercise["cefr"],
        modality="audio", feedback_type="immediate", experiment_group=user.experiment_group,
        delivery_group=user.delivery_group, prompt=exercise["question"], response=payload.answer,
        expected_answer=exercise["answer"], correct=correct, score=score, xp_earned=10 if correct else 3,
        engagement_seconds=max(10, payload.playback_count * 8),
    ))
    update_mastery(db, user, user.selected_language, "listening", score)
    user.xp += 10 if correct else 3
    db.commit()
    return {"correct": correct, "score": score, "answer": exercise["answer"], "feedback": "Strong listening recall." if correct else "Replay slowly, then listen once without the transcript."}


def process_practice_job(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(AIJob).filter(AIJob.id == job_id).first()
        if not job or job.status not in {"queued", "retrying"}:
            return
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.attempts += 1
        db.commit()
        user = db.query(User).filter(User.id == job.user_id).first()
        mastery = mastery_snapshot(db, user)
        weak = [item["skill"] for item in sorted(mastery, key=lambda x: x["mastery"])[:2]]
        terms = [row.term for row in db.query(ReviewItem).filter(ReviewItem.user_id == user.id).order_by(ReviewItem.next_review_at).limit(8)]
        result = ai_service.generate_personalized_practice(user.selected_language, user.cefr_level, weak, terms)
        if not result.get("exercises"):
            raise RuntimeError(result.get("error", "No valid exercises returned"))
        persisted = []
        for exercise in result["exercises"]:
            content_hash = hashlib.sha256(str(exercise).encode()).hexdigest()
            row = db.query(GeneratedExercise).filter(GeneratedExercise.content_hash == content_hash, GeneratedExercise.user_id == user.id).first()
            if not row:
                row = GeneratedExercise(
                    id=f"gen-{uuid4().hex[:16]}", user_id=user.id, language_code=user.selected_language,
                    skill=exercise["skill"], cefr_level=user.cefr_level, content_hash=content_hash, payload=exercise,
                )
                db.add(row)
            persisted.append({**exercise, "id": row.id})
        result["exercises"] = persisted
        record_usage(db, user.id, "personalized-practice", result.pop("_usage", None))
        job.result = result
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.query(AIJob).filter(AIJob.id == job_id).first()
        if job:
            job.error = type(exc).__name__
            job.status = "retrying" if job.attempts < job.max_attempts else "failed"
            db.commit()
    finally:
        db.close()


def process_pronunciation_job(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(AIJob).filter(AIJob.id == job_id).first()
        if not job or job.status not in {"queued", "retrying"}:
            return
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.attempts += 1
        db.commit()
        user = db.query(User).filter(User.id == job.user_id).first()
        audio_bytes = base64.b64decode(job.payload["audio_base64"])
        transcript = ai_service.transcribe_audio(audio_bytes, job.payload["filename"])
        comparison = compare_words(job.payload["target"], str(transcript))
        score = comparison["score"]
        xp = 15 if score >= 80 else 8 if score >= 55 else 3
        user.xp += xp
        db.add(Interaction(
            user_id=user.id, language_code=job.payload["language_code"], interaction_type="pronunciation",
            skill="speaking", proficiency_snapshot=user.proficiency, task_complexity="adaptive",
            modality="audio", feedback_type="word-level", experiment_group=user.experiment_group,
            delivery_group=user.delivery_group, prompt=job.payload["target"], response=str(transcript),
            expected_answer=job.payload["target"], correct=score >= 70, score=score, xp_earned=xp,
            engagement_seconds=job.payload["engagement_seconds"],
        ))
        update_mastery(db, user, job.payload["language_code"], "speaking", score)
        job.result = {
            "transcript": str(transcript), "score": score,
            "feedback": "Clear pronunciation." if score >= 80 else "Try again slowly and match each word." if score >= 55 else "Listen once more and repeat in shorter parts.",
            "word_feedback": comparison["words"], "disclaimer": comparison["disclaimer"],
            "xp_awarded": xp, "total_xp": user.xp,
        }
        job.payload = {"processed": True}
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.query(AIJob).filter(AIJob.id == job_id).first()
        if job:
            job.error = type(exc).__name__
            job.status = "retrying" if job.attempts < job.max_attempts else "failed"
            db.commit()
    finally:
        db.close()


def process_job(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(AIJob).filter(AIJob.id == job_id).first()
        job_type = job.job_type if job else ""
    finally:
        db.close()
    if job_type == "personalized-practice":
        process_practice_job(job_id)
    elif job_type == "pronunciation":
        process_pronunciation_job(job_id)


@router.post("/practice-jobs", status_code=202)
def create_practice_job(payload: PracticeJobRequest, background: BackgroundTasks, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    enforce_rate_limit(request, "ai-practice", user.id)
    existing = db.query(AIJob).filter(AIJob.idempotency_key == f"{user.id}:{payload.idempotency_key}").first()
    if existing:
        return {"job_id": existing.id, "status": existing.status, "idempotent_replay": True}
    job = AIJob(id=uuid4().hex, user_id=user.id, job_type="personalized-practice", idempotency_key=f"{user.id}:{payload.idempotency_key}", payload={})
    db.add(job)
    db.commit()
    background.add_task(process_job, job.id)
    return {"job_id": job.id, "status": job.status, "idempotent_replay": False}


@router.post("/pronunciation-jobs", status_code=202)
async def create_pronunciation_job(
    background: BackgroundTasks,
    request: Request,
    audio: UploadFile = File(...),
    target: str = Form(..., min_length=1, max_length=500),
    language_code: str = Form(...),
    engagement_seconds: int = Form(default=30, ge=1, le=3600),
    idempotency_key: str = Form(..., min_length=8, max_length=120),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    enforce_rate_limit(request, "ai-pronunciation", user.id, limit=8)
    if language_code not in LISTENING_EXERCISES:
        raise HTTPException(status_code=422, detail="Unsupported language")
    existing = db.query(AIJob).filter(AIJob.idempotency_key == f"{user.id}:{idempotency_key}").first()
    if existing:
        return {"job_id": existing.id, "status": existing.status, "idempotent_replay": True}
    audio_bytes = await audio.read()
    if not audio_bytes or len(audio_bytes) > min(settings.max_audio_bytes, 4 * 1024 * 1024):
        raise HTTPException(status_code=422, detail="Async pronunciation audio must be between 1 byte and 4 MB")
    job = AIJob(
        id=uuid4().hex, user_id=user.id, job_type="pronunciation",
        idempotency_key=f"{user.id}:{idempotency_key}",
        payload={
            "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
            "filename": audio.filename or "pronunciation.webm",
            "target": target, "language_code": language_code, "engagement_seconds": engagement_seconds,
        },
    )
    db.add(job)
    db.commit()
    background.add_task(process_job, job.id)
    return {"job_id": job.id, "status": job.status, "idempotent_replay": False}


@router.get("/jobs/{job_id}")
def job_status(job_id: str, background: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.query(AIJob).filter(AIJob.id == job_id, AIJob.user_id == user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == "retrying" and job.attempts < job.max_attempts:
        background.add_task(process_job, job.id)
    return {"job_id": job.id, "type": job.job_type, "status": job.status, "result": job.result, "error": job.error, "attempts": job.attempts}


@router.post("/generated-exercises/{exercise_id}/submit")
def submit_generated_exercise(
    exercise_id: str,
    payload: GeneratedExerciseSubmission,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exercise = db.query(GeneratedExercise).filter(
        GeneratedExercise.id == exercise_id,
        GeneratedExercise.user_id == user.id,
        GeneratedExercise.approved.is_(True),
    ).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Generated exercise not found")
    expected = str(exercise.payload["answer"])
    correct = payload.answer.strip().casefold() == expected.strip().casefold()
    score = 100 if correct else 25
    prior_correct = db.query(Interaction).filter(
        Interaction.user_id == user.id,
        Interaction.interaction_type == "generated-exercise",
        Interaction.prompt == exercise.payload["prompt"],
        Interaction.correct.is_(True),
    ).first()
    xp = (0 if prior_correct else 12) if correct else 2
    user.xp += xp
    db.add(Interaction(
        user_id=user.id, language_code=exercise.language_code, interaction_type="generated-exercise",
        skill=exercise.skill, proficiency_snapshot=user.proficiency, task_complexity=exercise.payload["complexity"],
        modality="text", feedback_type="personalized", experiment_group=user.experiment_group,
        delivery_group=user.delivery_group, prompt=exercise.payload["prompt"], response=payload.answer,
        expected_answer=expected, correct=correct, score=score, xp_earned=xp,
        engagement_seconds=payload.engagement_seconds,
    ))
    update_mastery(db, user, exercise.language_code, exercise.skill, score)
    db.commit()
    return {"correct": correct, "expected_answer": expected, "feedback": exercise.payload["explanation"], "xp_awarded": xp}


@router.post("/researcher-invitations")
def invite_researcher(payload: InvitationRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_researcher(user)
    raw = generate_opaque_token()
    invitation = ResearcherInvitation(
        email=payload.email.lower().strip(), token_hash=token_hash(raw), invited_by_user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(hours=payload.expires_hours),
    )
    db.add(invitation)
    db.add(AuditLog(user_id=user.id, action="researcher.invited", resource_type="researcher_invitation", resource_id=payload.email))
    db.commit()
    send_transactional_email(
        invitation.email,
        "LinguaLeap AI researcher invitation",
        f'<p>You were invited to the LinguaLeap research console.</p><p><code>{raw}</code></p>',
    )
    response = {"email": invitation.email, "expires_at": invitation.expires_at}
    if settings.email_delivery_mode == "console" and settings.environment != "production":
        response["invitation_token"] = raw
    return response


@router.get("/experiments")
def experiments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_researcher(user)
    return [{
        "id": row.id, "name": row.name, "hypothesis": row.hypothesis, "version": row.version,
        "status": row.status, "starts_at": row.starts_at, "ends_at": row.ends_at,
        "configuration": row.configuration, "frozen_at": row.frozen_at,
        "enrollment_count": db.query(ExperimentEnrollment).filter(ExperimentEnrollment.experiment_id == row.id).count(),
    } for row in db.query(Experiment).order_by(Experiment.created_at.desc()).all()]


@router.post("/experiments", status_code=201)
def create_experiment(payload: ExperimentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_researcher(user)
    experiment = Experiment(**payload.model_dump(), created_by_user_id=user.id)
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return {"id": experiment.id, "status": experiment.status}


@router.post("/experiments/{experiment_id}/activate")
def activate_experiment(experiment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_researcher(user)
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.status != "draft":
        raise HTTPException(status_code=409, detail="Only draft experiments can be activated")
    experiment.status = "active"
    experiment.frozen_at = datetime.utcnow()
    experiment.starts_at = experiment.starts_at or datetime.utcnow()
    db.commit()
    return {"id": experiment.id, "status": experiment.status, "frozen_at": experiment.frozen_at}


@router.post("/experiments/{experiment_id}/enroll")
def enroll_experiment(experiment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.research_consent:
        raise HTTPException(status_code=409, detail="Research consent is required")
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id, Experiment.status == "active").first()
    if not experiment or (experiment.ends_at and experiment.ends_at <= datetime.utcnow()):
        raise HTTPException(status_code=404, detail="Active experiment not found")
    existing = db.query(ExperimentEnrollment).filter(
        ExperimentEnrollment.experiment_id == experiment.id,
        ExperimentEnrollment.user_id == user.id,
    ).first()
    if existing:
        return {"experiment_group": existing.experiment_group, "delivery_group": existing.delivery_group, "assignment_locked": True}
    digest = hmac.new(settings.secret_key.encode(), f"{experiment.id}:{user.anonymous_id}".encode(), hashlib.sha256).hexdigest()
    tutor_groups = experiment.configuration.get("tutor_groups", ["llm_tutor", "structured_baseline"])
    delivery_groups = experiment.configuration.get("delivery_groups", ["text_only", "multimodal"])
    enrollment = ExperimentEnrollment(
        experiment_id=experiment.id, user_id=user.id,
        experiment_group=tutor_groups[int(digest[:8], 16) % len(tutor_groups)],
        delivery_group=delivery_groups[int(digest[8:16], 16) % len(delivery_groups)],
        assignment_digest=digest,
    )
    db.add(enrollment)
    db.commit()
    return {"experiment_group": enrollment.experiment_group, "delivery_group": enrollment.delivery_group, "assignment_locked": True}


def ci95(values):
    if len(values) < 2:
        return None
    margin = 1.96 * pstdev(values) / math.sqrt(len(values))
    center = mean(values)
    return [round(center - margin, 2), round(center + margin, 2)]


def cohens_d(left, right):
    if len(left) < 2 or len(right) < 2:
        return None
    pooled = math.sqrt((pstdev(left) ** 2 + pstdev(right) ** 2) / 2)
    return round((mean(left) - mean(right)) / pooled, 3) if pooled else 0


@router.get("/research-quality")
def research_quality(
    language: str | None = Query(default=None),
    proficiency: str | None = Query(default=None),
    skill: str | None = Query(default=None),
    experiment_group: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_researcher(user)
    participants = db.query(User).filter(User.research_consent.is_(True)).all()
    query = db.query(Interaction).join(User).filter(User.research_consent.is_(True), Interaction.is_simulated.is_(False))
    if language:
        query = query.filter(Interaction.language_code == language)
    if proficiency:
        query = query.filter(Interaction.proficiency_snapshot == proficiency)
    if skill:
        query = query.filter(Interaction.skill == skill)
    if experiment_group:
        query = query.filter(Interaction.experiment_group == experiment_group)
    if date_from:
        query = query.filter(Interaction.created_at >= date_from)
    if date_to:
        query = query.filter(Interaction.created_at <= date_to)
    observed = query.all()
    groups = {
        name: [row.score for row in observed if row.experiment_group == name]
        for name in ["llm_tutor", "structured_baseline"]
    }
    missing_post = sum(1 for row in participants if row.post_test_score is None)
    inactive = sum(1 for row in participants if not any(item.user_id == row.id for item in observed))
    participant_interactions = {participant.id: [row for row in observed if row.user_id == participant.id] for participant in participants}
    started = sum(1 for rows in participant_interactions.values() if rows)
    practiced = sum(1 for rows in participant_interactions.values() if len(rows) >= 3)
    assessed = sum(1 for participant in participants if participant.post_test_score is not None)
    cohort_counts = {}
    for row in observed:
        week = row.created_at.strftime("%Y-W%W") if row.created_at else "unknown"
        cohort_counts.setdefault(week, set()).add(row.user_id)
    return {
        "filters": {
            "language": language, "proficiency": proficiency, "skill": skill,
            "experiment_group": experiment_group, "date_from": date_from, "date_to": date_to,
        },
        "sample": {"participants": len(participants), "observed_interactions": len(observed), "missing_post_tests": missing_post, "inactive_participants": inactive},
        "groups": {
            key: {"n": len(values), "mean": round(mean(values), 2) if values else None, "confidence_interval_95": ci95(values)}
            for key, values in groups.items()
        },
        "effect_size_cohens_d": cohens_d(groups["llm_tutor"], groups["structured_baseline"]),
        "attrition_rate": round(inactive / len(participants) * 100, 1) if participants else 0,
        "data_completeness": round((1 - missing_post / len(participants)) * 100, 1) if participants else 0,
        "completion_funnel": {
            "consented": len(participants),
            "started": started,
            "three_or_more_interactions": practiced,
            "post_test_complete": assessed,
        },
        "cohorts": [{"week": key, "active_participants": len(value)} for key, value in sorted(cohort_counts.items())],
        "warnings": [
            warning for warning in [
                "Sample size is too small for defensible inference." if len(participants) < 30 else "",
                "At least one comparison group has fewer than 10 observations." if any(len(v) < 10 for v in groups.values()) else "",
                "Missing post-tests can bias learning-gain estimates." if missing_post else "",
            ] if warning
        ],
    }


@router.get("/usage")
def provider_usage(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_researcher(user)
    rows = db.query(ProviderUsage).all()
    return {
        "requests": len(rows),
        "failed_requests": sum(1 for row in rows if not row.success),
        "prompt_tokens": sum(row.prompt_tokens for row in rows),
        "completion_tokens": sum(row.completion_tokens for row in rows),
        "estimated_cost_usd": round(sum(row.estimated_cost_usd for row in rows), 6),
        "average_latency_ms": round(mean([row.latency_ms for row in rows])) if rows else 0,
    }
