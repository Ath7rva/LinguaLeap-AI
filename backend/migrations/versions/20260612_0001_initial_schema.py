"""Create the LinguaLeap learning and research schema."""

from alembic import op
import sqlalchemy as sa

revision = "20260612_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("anonymous_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="learner"),
        sa.Column("proficiency", sa.String(), nullable=False, server_default="beginner"),
        sa.Column("learning_goal", sa.String(), nullable=False, server_default="Everyday conversation"),
        sa.Column("selected_language", sa.String(), nullable=False, server_default="hi"),
        sa.Column("experiment_group", sa.String(), nullable=False, server_default="not_enrolled"),
        sa.Column("delivery_group", sa.String(), nullable=False, server_default="not_enrolled"),
        sa.Column("research_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consented_at", sa.DateTime()),
        sa.Column("pre_test_score", sa.Float()),
        sa.Column("post_test_score", sa.Float()),
        sa.Column("xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("streak", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_active", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("anonymous_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_anonymous_id", "users", ["anonymous_id"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "memory_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.Column("vocab_focus", sa.Text(), server_default=""),
        sa.Column("grammar_focus", sa.Text(), server_default=""),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("lesson_id", sa.String(), nullable=False),
        sa.Column("language_code", sa.String(), nullable=False),
        sa.Column("completed", sa.Boolean(), server_default=sa.false()),
        sa.Column("score", sa.Float(), server_default="0"),
        sa.Column("completed_at", sa.DateTime()),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),
    )
    op.create_table(
        "interactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("language_code", sa.String(), nullable=False),
        sa.Column("interaction_type", sa.String(), nullable=False),
        sa.Column("skill", sa.String(), nullable=False, server_default="vocabulary"),
        sa.Column("proficiency_snapshot", sa.String(), nullable=False, server_default="beginner"),
        sa.Column("task_complexity", sa.String(), nullable=False, server_default="basic"),
        sa.Column("modality", sa.String(), nullable=False, server_default="text"),
        sa.Column("feedback_type", sa.String(), nullable=False, server_default="adaptive"),
        sa.Column("experiment_group", sa.String(), nullable=False, server_default="not_enrolled"),
        sa.Column("delivery_group", sa.String(), nullable=False, server_default="not_enrolled"),
        sa.Column("prompt", sa.Text(), server_default=""),
        sa.Column("response", sa.Text(), server_default=""),
        sa.Column("expected_answer", sa.Text(), server_default=""),
        sa.Column("correct", sa.Boolean(), server_default=sa.true()),
        sa.Column("score", sa.Float(), server_default="0"),
        sa.Column("pre_test_score", sa.Float()),
        sa.Column("post_test_score", sa.Float()),
        sa.Column("xp_earned", sa.Integer(), server_default="0"),
        sa.Column("engagement_seconds", sa.Integer(), server_default="30"),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "review_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("language_code", sa.String(), nullable=False),
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("translation", sa.String(), server_default=""),
        sa.Column("difficulty", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("repetition", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_quality", sa.Integer()),
        sa.Column("last_reviewed_at", sa.DateTime()),
        sa.Column("next_review_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "language_code", "term", name="uq_user_review_term"),
    )


def downgrade():
    op.drop_table("review_items")
    op.drop_table("interactions")
    op.drop_table("lesson_progress")
    op.drop_table("memory_profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_anonymous_id", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
