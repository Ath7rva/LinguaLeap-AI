from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.api.routes.auth import experiment_assignment
from app.core.security import hash_password
from app.models import Interaction, MemoryProfile, ReviewItem, User


DEMO_USERS = [
    ("Asha", "demo.asha@example.test", "hi", "beginner", 38, 72),
    ("Mina", "demo.mina@example.test", "ja", "beginner", 42, 69),
    ("Jonas", "demo.jonas@example.test", "de", "intermediate", 55, 78),
    ("Ravi", "demo.ravi@example.test", "hi", "intermediate", 58, 82),
    ("Emi", "demo.emi@example.test", "ja", "advanced", 66, 84),
    ("Lena", "demo.lena@example.test", "de", "beginner", 35, 64),
    ("Noah", "demo.noah@example.test", "de", "intermediate", 51, 75),
    ("Priya", "demo.priya@example.test", "hi", "advanced", 69, 88),
]


def seed_demo_data(db: Session):
    if db.query(User).filter(User.email.like("demo.%@example.test")).first():
        return

    now = datetime.utcnow()
    for index, (name, email, language, proficiency, pre_score, post_score) in enumerate(DEMO_USERS):
        experiment_group, delivery_group = experiment_assignment(email, True)
        user = User(
            anonymous_id=f"DEMO-{index + 1:03d}",
            email=email,
            name=name,
            password_hash=hash_password("DemoPass123!"),
            proficiency=proficiency,
            learning_goal="Everyday conversation",
            selected_language=language,
            experiment_group=experiment_group,
            delivery_group=delivery_group,
            research_consent=True,
            consented_at=now - timedelta(days=40),
            pre_test_score=pre_score,
            post_test_score=post_score,
            xp=180 + index * 45,
            streak=2 + index % 6,
        )
        db.add(user)
        db.flush()
        db.add(MemoryProfile(user_id=user.id, notes="Simulated learner used only for product demonstration."))

        score_offset = 8 if experiment_group == "llm_tutor" else 0
        modality_offset = 5 if delivery_group == "multimodal" else 0
        for session in range(8):
            score = min(98, 48 + session * 4 + score_offset + modality_offset + index % 5)
            db.add(Interaction(
                user_id=user.id,
                language_code=language,
                interaction_type=["exercise", "tutor", "review"][session % 3],
                skill=["vocabulary", "speaking", "writing", "grammar"][session % 4],
                proficiency_snapshot=proficiency,
                task_complexity=["basic", "intermediate", "adaptive"][session % 3],
                modality="text" if delivery_group == "text_only" else ["text", "audio"][session % 2],
                feedback_type="structured" if experiment_group == "structured_baseline" else "adaptive",
                experiment_group=experiment_group,
                delivery_group=delivery_group,
                prompt="Simulated demonstration interaction",
                response="Simulated demonstration response",
                correct=score >= 65,
                score=score,
                pre_test_score=pre_score,
                post_test_score=post_score,
                xp_earned=10,
                engagement_seconds=35 + session * 5 + index,
                is_simulated=True,
                created_at=now - timedelta(days=28 - session * 3),
            ))

        db.add(ReviewItem(
            user_id=user.id,
            language_code=language,
            term={"hi": "पानी", "de": "Wasser", "ja": "水"}[language],
            translation="water",
            difficulty=2.4,
            interval_days=6,
            repetition=2,
            last_quality=3 + index % 3,
            last_reviewed_at=now - timedelta(days=5),
            next_review_at=now + timedelta(days=1),
        ))
    db.commit()
