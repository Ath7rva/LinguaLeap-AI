from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    anonymous_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="learner", nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    token_version = Column(Integer, default=1, nullable=False)
    proficiency = Column(String, default="beginner", nullable=False)
    cefr_level = Column(String, default="A1", nullable=False)
    placement_score = Column(Float)
    learning_goal = Column(String, default="Everyday conversation", nullable=False)
    selected_language = Column(String, default="hi", nullable=False)
    experiment_group = Column(String, default="not_enrolled", nullable=False)
    delivery_group = Column(String, default="not_enrolled", nullable=False)
    research_consent = Column(Boolean, default=False, nullable=False)
    consented_at = Column(DateTime)
    pre_test_score = Column(Float)
    post_test_score = Column(Float)
    xp = Column(Integer, default=0, nullable=False)
    streak = Column(Integer, default=1, nullable=False)
    last_active = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())

    memory_profile = relationship("MemoryProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")
    lesson_progress = relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan")
    review_items = relationship("ReviewItem", back_populates="user", cascade="all, delete-orphan")
    skill_mastery = relationship("SkillMastery", back_populates="user", cascade="all, delete-orphan")


class MemoryProfile(Base):
    __tablename__ = "memory_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    notes = Column(Text, default="")
    vocab_focus = Column(Text, default="")
    grammar_focus = Column(Text, default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="memory_profile")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(String, nullable=False)
    language_code = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    score = Column(Float, default=0.0)
    completed_at = Column(DateTime)

    user = relationship("User", back_populates="lesson_progress")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language_code = Column(String, nullable=False)
    interaction_type = Column(String, nullable=False)
    skill = Column(String, default="vocabulary", nullable=False)
    proficiency_snapshot = Column(String, default="beginner", nullable=False)
    task_complexity = Column(String, default="basic", nullable=False)
    modality = Column(String, default="text", nullable=False)
    feedback_type = Column(String, default="adaptive", nullable=False)
    experiment_group = Column(String, default="not_enrolled", nullable=False)
    delivery_group = Column(String, default="not_enrolled", nullable=False)
    prompt = Column(Text, default="")
    response = Column(Text, default="")
    expected_answer = Column(Text, default="")
    correct = Column(Boolean, default=True)
    score = Column(Float, default=0.0)
    pre_test_score = Column(Float)
    post_test_score = Column(Float)
    xp_earned = Column(Integer, default=0)
    engagement_seconds = Column(Integer, default=30)
    is_simulated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="interactions")


class ReviewItem(Base):
    __tablename__ = "review_items"
    __table_args__ = (UniqueConstraint("user_id", "language_code", "term", name="uq_user_review_term"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    language_code = Column(String, nullable=False)
    term = Column(String, nullable=False)
    translation = Column(String, default="")
    difficulty = Column(Float, default=2.5, nullable=False)
    interval_days = Column(Integer, default=1, nullable=False)
    repetition = Column(Integer, default=0, nullable=False)
    last_quality = Column(Integer)
    last_reviewed_at = Column(DateTime)
    next_review_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="review_items")


class SkillMastery(Base):
    __tablename__ = "skill_mastery"
    __table_args__ = (UniqueConstraint("user_id", "language_code", "skill", name="uq_user_language_skill"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    language_code = Column(String, nullable=False)
    skill = Column(String, nullable=False)
    mastery = Column(Float, default=0.0, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    correct_attempts = Column(Integer, default=0, nullable=False)
    last_practiced_at = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="skill_mastery")


class ListeningAttempt(Base):
    __tablename__ = "listening_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    exercise_id = Column(String, nullable=False)
    language_code = Column(String, nullable=False)
    answer = Column(Text, default="")
    correct = Column(Boolean, default=False, nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    playback_count = Column(Integer, default=1, nullable=False)
    transcript_revealed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class AIJob(Base):
    __tablename__ = "ai_jobs"

    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_type = Column(String, nullable=False)
    status = Column(String, default="queued", nullable=False, index=True)
    idempotency_key = Column(String, nullable=False, unique=True, index=True)
    payload = Column(JSON, default=dict, nullable=False)
    result = Column(JSON)
    error = Column(Text, default="")
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    user_agent = Column(String, default="")
    ip_address = Column(String, default="")
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class OneTimeToken(Base):
    __tablename__ = "one_time_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    purpose = Column(String, nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class ResearcherInvitation(Base):
    __tablename__ = "researcher_invitations"

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    invited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    hypothesis = Column(Text, default="")
    version = Column(String, default="1.0", nullable=False)
    status = Column(String, default="draft", nullable=False, index=True)
    starts_at = Column(DateTime)
    ends_at = Column(DateTime)
    configuration = Column(JSON, default=dict, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    frozen_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class ExperimentEnrollment(Base):
    __tablename__ = "experiment_enrollments"
    __table_args__ = (UniqueConstraint("experiment_id", "user_id", name="uq_experiment_user"),)

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    experiment_group = Column(String, nullable=False)
    delivery_group = Column(String, nullable=False)
    assignment_digest = Column(String, nullable=False)
    enrolled_at = Column(DateTime, server_default=func.now())
    withdrawn_at = Column(DateTime)


class ProviderUsage(Base):
    __tablename__ = "provider_usage"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    provider = Column(String, nullable=False)
    operation = Column(String, nullable=False)
    model = Column(String, default="")
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    success = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    action = Column(String, nullable=False, index=True)
    resource_type = Column(String, default="")
    resource_id = Column(String, default="")
    request_id = Column(String, default="", index=True)
    ip_address = Column(String, default="")
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class GeneratedExercise(Base):
    __tablename__ = "generated_exercises"

    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    language_code = Column(String, nullable=False)
    skill = Column(String, nullable=False)
    cefr_level = Column(String, nullable=False)
    content_hash = Column(String, nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    approved = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
