from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Interaction, LessonProgress, ReviewItem, SkillMastery, User
from app.services.content import CURRICULUM

CEFR_ORDER = ["A1", "A2", "B1"]
SKILLS = ["vocabulary", "grammar", "listening", "speaking", "writing", "translation"]


def cefr_from_placement(score: float) -> str:
    if score >= 75:
        return "B1"
    if score >= 45:
        return "A2"
    return "A1"


def update_mastery(db: Session, user: User, language_code: str, skill: str, score: float):
    normalized = skill.split("-")[0] if skill else "vocabulary"
    row = db.query(SkillMastery).filter(
        SkillMastery.user_id == user.id,
        SkillMastery.language_code == language_code,
        SkillMastery.skill == normalized,
    ).first()
    if not row:
        row = SkillMastery(
            user_id=user.id, language_code=language_code, skill=normalized,
            mastery=0.0, attempts=0, correct_attempts=0,
        )
        db.add(row)
    row.attempts += 1
    row.correct_attempts += int(score >= 70)
    recent_weight = 0.35
    row.mastery = round(score if row.attempts == 1 else row.mastery * (1 - recent_weight) + score * recent_weight, 1)
    row.last_practiced_at = datetime.utcnow()
    return row


def mastery_snapshot(db: Session, user: User):
    rows = db.query(SkillMastery).filter(
        SkillMastery.user_id == user.id,
        SkillMastery.language_code == user.selected_language,
    ).all()
    values = {row.skill: row.mastery for row in rows}
    return [{"skill": skill, "mastery": values.get(skill, 0), "attempts": next((r.attempts for r in rows if r.skill == skill), 0)} for skill in SKILLS]


def recommendation(db: Session, user: User):
    mastery = mastery_snapshot(db, user)
    weakest = min(mastery, key=lambda item: (item["mastery"] if item["attempts"] else -1, item["attempts"]))
    completed = {
        row.lesson_id for row in db.query(LessonProgress).filter(
            LessonProgress.user_id == user.id,
            LessonProgress.completed.is_(True),
        ).all()
    }
    next_lesson = None
    for level in CURRICULUM[user.selected_language]:
        for lesson in level["lessons"]:
            if lesson["id"] not in completed and (not lesson.get("prerequisite") or lesson["prerequisite"] in completed):
                next_lesson = lesson
                break
        if next_lesson:
            break
    due = db.query(ReviewItem).filter(
        ReviewItem.user_id == user.id,
        ReviewItem.next_review_at <= datetime.utcnow(),
    ).count()
    if due:
        action = {"type": "review", "target": "spaced-review", "title": "Review due vocabulary"}
        reason = f"{due} memory items are due; retrieval practice has the highest immediate priority."
    elif weakest["attempts"] and weakest["mastery"] < 70:
        action = {"type": "practice", "target": weakest["skill"], "title": f"Strengthen {weakest['skill']}"}
        reason = f"{weakest['skill'].title()} is your lowest measured skill at {weakest['mastery']}% mastery."
    elif next_lesson:
        action = {"type": "lesson", "target": next_lesson["id"], "title": next_lesson["title"]}
        reason = "Your prerequisites are complete and this is the next lesson in the CEFR path."
    else:
        action = {"type": "practice", "target": "conversation", "title": "Conversation challenge"}
        reason = "Your current path is complete; mixed retrieval will maintain fluency."
    return {"action": action, "reason": reason, "weakest_skill": weakest, "cefr_level": user.cefr_level}


def learning_health(db: Session, user: User):
    interactions = db.query(Interaction).filter(Interaction.user_id == user.id).all()
    return {
        "mastery": mastery_snapshot(db, user),
        "recommendation": recommendation(db, user),
        "interaction_count": len(interactions),
    }
