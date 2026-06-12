from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
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
    proficiency = Column(String, default="beginner", nullable=False)
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
