import csv
import io
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.routes.auth import serialize_user
from app.api.routes.auth import experiment_assignment
from app.core.security import get_current_user
from app.database import get_db
from app.models import Interaction, LessonProgress, MemoryProfile, ReviewItem, User
from app.services import ai as ai_service
from app.services.analytics import grouped_metrics, interaction_metrics, observed_retention, research_summary, skill_metrics
from app.services.content import CURRICULUM, EXERCISES, LANGUAGES, find_exercise, find_lesson, language_by_code
from app.services.spaced_repetition import schedule_sm2

router = APIRouter(prefix="/platform", tags=["platform"])


class LanguageSelection(BaseModel):
    language_code: str


class ExerciseSubmission(BaseModel):
    exercise_id: str
    answer: str
    engagement_seconds: int = Field(default=30, ge=1, le=3600)


class TutorRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    language_code: str
    skill: str = "vocabulary"
    modality: str = "text"
    task_complexity: str = "basic"
    feedback_type: str = "adaptive"
    engagement_seconds: int = Field(default=30, ge=1, le=3600)


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1200)
    language_code: str
    engagement_seconds: int = Field(default=30, ge=1, le=3600)


class AssessmentSubmission(BaseModel):
    phase: str
    score: float = Field(ge=0, le=100)
    engagement_seconds: int = Field(default=30, ge=1, le=3600)


class ReviewSubmission(BaseModel):
    quality: int = Field(ge=0, le=5)
    engagement_seconds: int = Field(default=10, ge=1, le=3600)


class ConsentUpdate(BaseModel):
    research_consent: bool


def interaction_values(user: User):
    return {
        "proficiency_snapshot": user.proficiency,
        "experiment_group": user.experiment_group,
        "delivery_group": user.delivery_group,
        "pre_test_score": user.pre_test_score,
        "post_test_score": user.post_test_score,
    }


def stats_for(db: Session, user: User):
    interactions = db.query(Interaction).filter(Interaction.user_id == user.id).all()
    metrics = interaction_metrics(interactions)
    completed = db.query(LessonProgress).filter(
        LessonProgress.user_id == user.id, LessonProgress.completed.is_(True)
    ).count()
    due_reviews = db.query(ReviewItem).filter(
        ReviewItem.user_id == user.id, ReviewItem.next_review_at <= datetime.utcnow()
    ).count()
    effectiveness = round(
        metrics["accuracy"] * 0.45
        + metrics["mean_score"] * 0.35
        + min(completed * 10, 100) * 0.20
    )
    return {
        "total_interactions": metrics["n"],
        "accuracy": metrics["accuracy"],
        "average_score": metrics["mean_score"],
        "completed_lessons": completed,
        "engagement": metrics["mean_engagement_seconds"],
        "effectiveness": effectiveness,
        "due_reviews": due_reviews,
    }


def add_review_item(db: Session, user: User, language_code: str, term: str, translation: str = ""):
    term = term.strip()[:120]
    if not term:
        return
    existing = db.query(ReviewItem).filter(
        ReviewItem.user_id == user.id,
        ReviewItem.language_code == language_code,
        ReviewItem.term == term,
    ).first()
    if not existing:
        db.add(ReviewItem(
            user_id=user.id,
            language_code=language_code,
            term=term,
            translation=translation[:240],
            next_review_at=datetime.utcnow() + timedelta(days=1),
        ))


@router.get("/bootstrap")
def bootstrap(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"user": serialize_user(user), "languages": LANGUAGES, "dashboard": dashboard(db, user)}


@router.post("/language")
def select_language(payload: LanguageSelection, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.language_code not in {language["code"] for language in LANGUAGES}:
        raise HTTPException(status_code=422, detail="Unsupported language")
    user.selected_language = payload.language_code
    db.commit()
    return {"user": serialize_user(user), "language": language_by_code(payload.language_code)}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    metrics = stats_for(db, user)
    selected = language_by_code(user.selected_language)
    return {
        "metrics": metrics,
        "language": selected,
        "level": user.proficiency.title(),
        "next_lesson": CURRICULUM[user.selected_language][0]["lessons"][0],
        "daily_word": {
            "hi": {"word": "रोटी", "romanization": "Roti", "meaning": "Bread"},
            "de": {"word": "Reise", "romanization": "RY-zuh", "meaning": "Journey"},
            "ja": {"word": "旅", "romanization": "Tabi", "meaning": "Journey"},
        }[user.selected_language],
        "challenge": {
            "title": "Review Rescue" if metrics["due_reviews"] else "Conversation Sprint",
            "description": f"{metrics['due_reviews']} memory items are due today." if metrics["due_reviews"] else "Complete one tutor exchange and one structured exercise.",
            "reward": 30,
        },
        "experiment": {
            "enrolled": user.research_consent,
            "experiment_group": user.experiment_group,
            "delivery_group": user.delivery_group,
        },
    }


@router.get("/curriculum")
def curriculum(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    progress = {
        item.lesson_id: {"completed": item.completed, "score": item.score}
        for item in db.query(LessonProgress).filter(LessonProgress.user_id == user.id).all()
    }
    levels = []
    for level in CURRICULUM[user.selected_language]:
        lessons = [{**lesson, **progress.get(lesson["id"], {"completed": False, "score": 0})} for lesson in level["lessons"]]
        unlocked = level["level"] == 1 or all(item["completed"] for item in levels[-1]["lessons"])
        levels.append({**level, "lessons": lessons, "unlocked": unlocked, "completed_count": sum(1 for item in lessons if item["completed"])})
    return {"language": language_by_code(user.selected_language), "levels": levels}


@router.get("/lessons/{lesson_id}")
def lesson_detail(lesson_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    found = find_lesson(lesson_id)
    if not found:
        raise HTTPException(status_code=404, detail="Lesson not found")
    language_code, _, lesson = found
    if language_code != user.selected_language:
        raise HTTPException(status_code=409, detail="Select this lesson's language first")
    prerequisite = lesson.get("prerequisite")
    if prerequisite:
        completed = db.query(LessonProgress).filter(
            LessonProgress.user_id == user.id,
            LessonProgress.lesson_id == prerequisite,
            LessonProgress.completed.is_(True),
        ).first()
        if not completed:
            raise HTTPException(status_code=409, detail="Complete the prerequisite lesson first")
    return {"language": language_by_code(language_code), "lesson": lesson}


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(
    lesson_id: str,
    engagement_seconds: int = Body(default=180, embed=True, ge=1, le=3600),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    found = find_lesson(lesson_id)
    if not found:
        raise HTTPException(status_code=404, detail="Lesson not found")
    language_code, level, lesson = found
    if language_code != user.selected_language:
        raise HTTPException(status_code=409, detail="Select this lesson's language first")
    prerequisite = lesson.get("prerequisite")
    if prerequisite:
        completed = db.query(LessonProgress).filter(
            LessonProgress.user_id == user.id,
            LessonProgress.lesson_id == prerequisite,
            LessonProgress.completed.is_(True),
        ).first()
        if not completed:
            raise HTTPException(status_code=409, detail="Complete the prerequisite lesson first")
    if level["level"] > 1:
        prior = CURRICULUM[language_code][level["level"] - 2]["lessons"]
        completed_ids = {
            item.lesson_id for item in db.query(LessonProgress).filter(
                LessonProgress.user_id == user.id, LessonProgress.completed.is_(True)
            ).all()
        }
        if not all(item["id"] in completed_ids for item in prior):
            raise HTTPException(status_code=409, detail="Complete the previous level first")
    record = db.query(LessonProgress).filter(
        LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id
    ).first() or LessonProgress(user_id=user.id, lesson_id=lesson_id, language_code=language_code)
    newly_completed = not record.completed
    record.completed = True
    record.score = 100
    record.completed_at = datetime.utcnow()
    db.add(record)
    if newly_completed:
        user.xp += lesson["xp"]
        db.add(Interaction(
            user_id=user.id, language_code=language_code, interaction_type="lesson",
            skill="structured-learning", task_complexity=lesson.get("complexity", "basic"),
            modality="multimodal" if user.delivery_group == "multimodal" else "text",
            feedback_type="structured", prompt=lesson["title"], response="Completed",
            correct=True, score=100, xp_earned=lesson["xp"], engagement_seconds=engagement_seconds,
            **interaction_values(user),
        ))
        for term in lesson.get("review_terms", []):
            add_review_item(db, user, language_code, term["term"], term["translation"])
    db.commit()
    return {"completed": True, "xp": user.xp, "xp_awarded": lesson["xp"] if newly_completed else 0}


@router.get("/exercises")
def exercises(user: User = Depends(get_current_user)):
    return {"language": language_by_code(user.selected_language), "exercises": EXERCISES[user.selected_language]}


@router.post("/exercises/submit")
def submit_exercise(payload: ExerciseSubmission, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    found = find_exercise(payload.exercise_id)
    if not found:
        raise HTTPException(status_code=404, detail="Exercise not found")
    language_code, exercise = found
    correct = payload.answer.strip().casefold() == exercise["answer"].strip().casefold()
    xp, score = (15, 100) if correct else (3, 25)
    user.xp += xp
    db.add(Interaction(
        user_id=user.id, language_code=language_code, interaction_type="exercise",
        skill=exercise["skill"], task_complexity=exercise["complexity"], modality="text",
        feedback_type="immediate", prompt=exercise["prompt"], response=payload.answer,
        expected_answer=exercise["answer"], correct=correct, score=score, xp_earned=xp,
        engagement_seconds=payload.engagement_seconds, **interaction_values(user),
    ))
    add_review_item(db, user, language_code, exercise["answer"], exercise["prompt"])
    db.commit()
    return {
        "correct": correct, "expected_answer": exercise["answer"],
        "feedback": "Excellent recall. Keep the pattern active." if correct else "Review the model answer, then try it again from memory.",
        "xp_awarded": xp, "total_xp": user.xp,
    }


@router.post("/tutor")
def tutor(payload: TutorRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.language_code not in {item["code"] for item in LANGUAGES}:
        raise HTTPException(status_code=422, detail="Unsupported language")
    profile = db.query(MemoryProfile).filter(MemoryProfile.user_id == user.id).first()
    if user.research_consent and user.experiment_group == "structured_baseline":
        result = ai_service.generate_structured_response(payload.message, payload.language_code)
    else:
        result = ai_service.generate_tutor_response(
            payload.message, payload.language_code,
            profile.notes if profile else "", profile.vocab_focus if profile else "", profile.grammar_focus if profile else "",
        )
    xp = int(result.get("xp_awarded", 5))
    correction = result.get("correction", "")
    score = 88 if not correction else 62
    user.xp += xp
    if profile:
        profile.vocab_focus = "; ".join(filter(None, [profile.vocab_focus, result.get("vocab_update", "")]))[-1500:]
        profile.grammar_focus = "; ".join(filter(None, [profile.grammar_focus, result.get("grammar_update", "")]))[-1500:]
    modality = "text" if user.delivery_group == "text_only" else payload.modality
    db.add(Interaction(
        user_id=user.id, language_code=payload.language_code, interaction_type="tutor",
        skill=payload.skill, task_complexity=payload.task_complexity, modality=modality,
        feedback_type=payload.feedback_type, prompt=payload.message, response=result.get("reply", ""),
        correct=not bool(correction), score=score, xp_earned=xp, engagement_seconds=payload.engagement_seconds,
        **interaction_values(user),
    ))
    if result.get("vocab_update"):
        add_review_item(db, user, payload.language_code, result["vocab_update"])
    db.commit()
    return {**result, "total_xp": user.xp, "score": score}


@router.post("/translate")
def translate(payload: TranslationRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.language_code not in {item["code"] for item in LANGUAGES}:
        raise HTTPException(status_code=422, detail="Unsupported language")
    result = ai_service.translate_text(payload.text, payload.language_code)
    db.add(Interaction(
        user_id=user.id, language_code=payload.language_code, interaction_type="translation",
        skill="translation", task_complexity="basic", modality="text", feedback_type="explanatory",
        prompt=payload.text, response=result["translation"], correct=True, score=75, xp_earned=5,
        engagement_seconds=payload.engagement_seconds, **interaction_values(user),
    ))
    user.xp += 5
    db.commit()
    return {**result, "xp_awarded": 5, "total_xp": user.xp}


@router.post("/pronunciation")
async def pronunciation(
    audio: UploadFile = File(...),
    target: str = Form(...),
    language_code: str = Form(...),
    engagement_seconds: int = Form(default=30, ge=1, le=3600),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if language_code not in {item["code"] for item in LANGUAGES}:
        raise HTTPException(status_code=422, detail="Unsupported language")
    audio_bytes = await audio.read()
    if not audio_bytes or len(audio_bytes) > 8 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="Audio must be between 1 byte and 8 MB")
    try:
        transcript = ai_service.transcribe_audio(audio_bytes, audio.filename or "audio.webm")
    except Exception:
        raise HTTPException(status_code=503, detail="Pronunciation service is temporarily unavailable")
    normalized_target = " ".join(target.casefold().split())
    normalized_transcript = " ".join(str(transcript).casefold().split())
    score = round(SequenceMatcher(None, normalized_target, normalized_transcript).ratio() * 100)
    xp = 15 if score >= 80 else 8 if score >= 55 else 3
    db.add(Interaction(
        user_id=user.id, language_code=language_code, interaction_type="pronunciation",
        skill="speaking", task_complexity="basic", modality="audio", feedback_type="immediate",
        prompt=target, response=str(transcript), expected_answer=target, correct=score >= 70,
        score=score, xp_earned=xp, engagement_seconds=engagement_seconds, **interaction_values(user),
    ))
    user.xp += xp
    db.commit()
    return {
        "transcript": transcript,
        "score": score,
        "feedback": "Clear pronunciation." if score >= 80 else "Try again slowly and match each syllable." if score >= 55 else "Listen to the model phrase and repeat in shorter parts.",
        "xp_awarded": xp,
        "total_xp": user.xp,
    }


@router.post("/assessment")
def submit_assessment(payload: AssessmentSubmission, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.phase not in {"pre", "post"}:
        raise HTTPException(status_code=422, detail="phase must be pre or post")
    if payload.phase == "pre":
        user.pre_test_score = payload.score
    else:
        user.post_test_score = payload.score
    db.add(Interaction(
        user_id=user.id, language_code=user.selected_language, interaction_type="assessment",
        skill="assessment", task_complexity="standardized", modality="text", feedback_type="score-only",
        prompt=f"{payload.phase}-test", response=str(payload.score), correct=True, score=payload.score,
        pre_test_score=user.pre_test_score, post_test_score=user.post_test_score,
        engagement_seconds=payload.engagement_seconds, proficiency_snapshot=user.proficiency,
        experiment_group=user.experiment_group, delivery_group=user.delivery_group,
    ))
    db.commit()
    return {"phase": payload.phase, "score": payload.score, "learning_gain": (user.post_test_score - user.pre_test_score) if user.pre_test_score is not None and user.post_test_score is not None else None}


@router.get("/reviews")
def reviews(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(ReviewItem).filter(ReviewItem.user_id == user.id).order_by(ReviewItem.next_review_at).all()
    return [{
        "id": item.id, "term": item.term, "translation": item.translation,
        "interval_days": item.interval_days, "repetition": item.repetition,
        "next_review_at": item.next_review_at, "due": item.next_review_at <= datetime.utcnow(),
    } for item in rows]


@router.post("/reviews/{review_id}")
def review(review_id: int, payload: ReviewSubmission, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(ReviewItem).filter(ReviewItem.id == review_id, ReviewItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    schedule = schedule_sm2(item.repetition, item.interval_days, item.difficulty, payload.quality)
    for key, value in schedule.items():
        setattr(item, key, value)
    score = payload.quality * 20
    db.add(Interaction(
        user_id=user.id, language_code=item.language_code, interaction_type="review",
        skill="vocabulary-recall", task_complexity="adaptive", modality="text", feedback_type="spaced-repetition",
        prompt=item.term, response=str(payload.quality), expected_answer=item.translation,
        correct=payload.quality >= 3, score=score, xp_earned=5, engagement_seconds=payload.engagement_seconds,
        **interaction_values(user),
    ))
    user.xp += 5
    db.commit()
    return {"next_review_at": item.next_review_at, "interval_days": item.interval_days, "difficulty": item.difficulty, "xp_awarded": 5}


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    interactions = db.query(Interaction).filter(Interaction.user_id == user.id).order_by(Interaction.created_at).all()
    reviews_data = db.query(ReviewItem).filter(ReviewItem.user_id == user.id).all()
    tp = sum(1 for item in interactions if item.correct and item.score >= 70)
    fp = sum(1 for item in interactions if not item.correct and item.score >= 70)
    tn = sum(1 for item in interactions if not item.correct and item.score < 70)
    fn = sum(1 for item in interactions if item.correct and item.score < 70)
    consented = [item for item in interactions if item.experiment_group != "not_enrolled"]
    return {
        "data_source": "observed-user-data",
        "metrics": stats_for(db, user),
        "confusion_matrix": {"true_positive": tp, "false_positive": fp, "true_negative": tn, "false_negative": fn},
        "retention_curve": observed_retention(interactions, reviews_data),
        "skill_scores": skill_metrics(interactions),
        "comparisons": {
            "experimental": grouped_metrics(consented, "experiment_group", ["llm_tutor", "structured_baseline"]),
            "delivery": grouped_metrics(consented, "delivery_group", ["text_only", "multimodal"]),
        },
        "assessment": {
            "pre_test_score": user.pre_test_score,
            "post_test_score": user.post_test_score,
            "learning_gain": user.post_test_score - user.pre_test_score if user.pre_test_score is not None and user.post_test_score is not None else None,
        },
    }


def require_researcher(user: User):
    if user.role != "researcher":
        raise HTTPException(status_code=403, detail="Research mode requires an @admin.local account")


@router.get("/research")
def research(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_researcher(user)
    users = db.query(User).all()
    interactions = db.query(Interaction).all()
    consented_interactions = [
        item for item in interactions
        if item.experiment_group != "not_enrolled" and not item.is_simulated
    ]
    simulated_interactions = [
        item for item in interactions
        if item.experiment_group != "not_enrolled" and item.is_simulated
    ]
    return {
        "data_source": {
            "observed": sum(1 for item in interactions if not item.is_simulated),
            "simulated": sum(1 for item in interactions if item.is_simulated),
            "note": "Simulated demo records are labeled and excluded from observed-only claims.",
        },
        "summary": research_summary(users, interactions),
        "experimental": grouped_metrics(consented_interactions, "experiment_group", ["llm_tutor", "structured_baseline"]),
        "delivery": grouped_metrics(consented_interactions, "delivery_group", ["text_only", "multimodal"]),
        "simulated_demo": {
            "experimental": grouped_metrics(simulated_interactions, "experiment_group", ["llm_tutor", "structured_baseline"]),
            "delivery": grouped_metrics(simulated_interactions, "delivery_group", ["text_only", "multimodal"]),
        },
        "moderators": {
            "language_distribution": [
                {"language": language["name"], "count": sum(1 for item in consented_interactions if item.language_code == language["code"])}
                for language in LANGUAGES
            ],
            "proficiency": grouped_metrics(consented_interactions, "proficiency_snapshot", ["beginner", "intermediate", "advanced"]),
            "task_complexity": grouped_metrics(consented_interactions, "task_complexity", ["basic", "intermediate", "advanced", "adaptive"]),
            "feedback_type": grouped_metrics(consented_interactions, "feedback_type", ["adaptive", "structured", "immediate", "spaced-repetition"]),
        },
    }


@router.get("/privacy")
def privacy(user: User = Depends(get_current_user)):
    return {
        "anonymous_id": user.anonymous_id,
        "research_consent": user.research_consent,
        "collected": [
            "learner profile and selected language",
            "lesson completion and quiz answers",
            "tutor prompts and responses",
            "skill, proficiency, task complexity, modality, feedback type, and session duration",
            "optional pre-test and post-test scores",
        ],
        "purpose": "Personalized learning, progress analytics, and consented educational research comparisons.",
        "rights": ["Download research data through an authorized researcher", "Delete your account and associated learning records"],
    }


@router.patch("/privacy/consent")
def update_consent(payload: ConsentUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user.research_consent = payload.research_consent
    user.consented_at = datetime.utcnow() if payload.research_consent else None
    user.experiment_group, user.delivery_group = experiment_assignment(user.email, payload.research_consent)
    if not payload.research_consent:
        db.query(Interaction).filter(Interaction.user_id == user.id).update({
            Interaction.experiment_group: "not_enrolled",
            Interaction.delivery_group: "not_enrolled",
        })
    db.commit()
    db.refresh(user)
    return {"user": serialize_user(user)}


@router.delete("/account", status_code=204)
def delete_account(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(user)
    db.commit()
    return Response(status_code=204)


@router.get("/account/export")
def export_account(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    interactions = db.query(Interaction).filter(Interaction.user_id == user.id).order_by(Interaction.created_at).all()
    reviews_data = db.query(ReviewItem).filter(ReviewItem.user_id == user.id).all()
    return {
        "profile": serialize_user(user),
        "interactions": [{
            "language": item.language_code,
            "type": item.interaction_type,
            "skill": item.skill,
            "complexity": item.task_complexity,
            "modality": item.modality,
            "feedback": item.feedback_type,
            "prompt": item.prompt,
            "response": item.response,
            "correct": item.correct,
            "score": item.score,
            "engagement_seconds": item.engagement_seconds,
            "created_at": item.created_at,
        } for item in interactions],
        "reviews": [{
            "language": item.language_code,
            "term": item.term,
            "translation": item.translation,
            "last_quality": item.last_quality,
            "next_review_at": item.next_review_at,
        } for item in reviews_data],
    }


@router.get("/research/export")
def export_research(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_researcher(user)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "anonymous_id", "language", "type", "skill", "proficiency", "complexity", "modality",
        "feedback", "experiment_group", "delivery_group", "correct", "score", "pre_test",
        "post_test", "xp", "engagement_seconds", "simulated", "created_at",
    ])
    rows = db.query(Interaction).join(User).filter(User.research_consent.is_(True)).order_by(Interaction.created_at).all()
    for item in rows:
        writer.writerow([
            item.user.anonymous_id, item.language_code, item.interaction_type, item.skill,
            item.proficiency_snapshot, item.task_complexity, item.modality, item.feedback_type,
            item.experiment_group, item.delivery_group, item.correct, item.score,
            item.pre_test_score, item.post_test_score, item.xp_earned, item.engagement_seconds,
            item.is_simulated, item.created_at,
        ])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=lingualeap-research.csv"})
