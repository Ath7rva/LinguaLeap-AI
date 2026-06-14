"""Add adaptive learning, security, jobs, experiments, and observability."""

from alembic import op
import sqlalchemy as sa


revision = "20260614_0002"
down_revision = "20260612_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("users", sa.Column("cefr_level", sa.String(), nullable=False, server_default="A1"))
    op.add_column("users", sa.Column("placement_score", sa.Float()))

    op.create_table(
        "skill_mastery",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("language_code", sa.String(), nullable=False),
        sa.Column("skill", sa.String(), nullable=False),
        sa.Column("mastery", sa.Float(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_practiced_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "language_code", "skill", name="uq_user_language_skill"),
    )
    op.create_index("ix_skill_mastery_user_id", "skill_mastery", ["user_id"])

    op.create_table(
        "listening_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("exercise_id", sa.String(), nullable=False),
        sa.Column("language_code", sa.String(), nullable=False),
        sa.Column("answer", sa.Text(), server_default=""),
        sa.Column("correct", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("playback_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("transcript_revealed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_listening_attempts_user_id", "listening_attempts", ["user_id"])

    op.create_table(
        "ai_jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="queued"),
        sa.Column("idempotency_key", sa.String(), nullable=False, unique=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON()),
        sa.Column("error", sa.Text(), server_default=""),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
    )
    op.create_index("ix_ai_jobs_user_id", "ai_jobs", ["user_id"])
    op.create_index("ix_ai_jobs_status", "ai_jobs", ["status"])
    op.create_index("ix_ai_jobs_idempotency_key", "ai_jobs", ["idempotency_key"])

    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True),
        sa.Column("user_agent", sa.String(), server_default=""),
        sa.Column("ip_address", sa.String(), server_default=""),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"])
    op.create_index("ix_refresh_sessions_token_hash", "refresh_sessions", ["token_hash"])

    op.create_table(
        "one_time_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_one_time_tokens_user_id", "one_time_tokens", ["user_id"])
    op.create_index("ix_one_time_tokens_purpose", "one_time_tokens", ["purpose"])
    op.create_index("ix_one_time_tokens_token_hash", "one_time_tokens", ["token_hash"])

    op.create_table(
        "researcher_invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True),
        sa.Column("invited_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_researcher_invitations_email", "researcher_invitations", ["email"])
    op.create_index("ix_researcher_invitations_token_hash", "researcher_invitations", ["token_hash"])

    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("hypothesis", sa.Text(), server_default=""),
        sa.Column("version", sa.String(), nullable=False, server_default="1.0"),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("starts_at", sa.DateTime()),
        sa.Column("ends_at", sa.DateTime()),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("frozen_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_experiments_status", "experiments", ["status"])

    op.create_table(
        "experiment_enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("experiment_group", sa.String(), nullable=False),
        sa.Column("delivery_group", sa.String(), nullable=False),
        sa.Column("assignment_digest", sa.String(), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("withdrawn_at", sa.DateTime()),
        sa.UniqueConstraint("experiment_id", "user_id", name="uq_experiment_user"),
    )
    op.create_index("ix_experiment_enrollments_experiment_id", "experiment_enrollments", ["experiment_id"])
    op.create_index("ix_experiment_enrollments_user_id", "experiment_enrollments", ["user_id"])

    op.create_table(
        "provider_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("operation", sa.String(), nullable=False),
        sa.Column("model", sa.String(), server_default=""),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_provider_usage_user_id", "provider_usage", ["user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), server_default=""),
        sa.Column("resource_id", sa.String(), server_default=""),
        sa.Column("request_id", sa.String(), server_default=""),
        sa.Column("ip_address", sa.String(), server_default=""),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])

    op.create_table(
        "generated_exercises",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("language_code", sa.String(), nullable=False),
        sa.Column("skill", sa.String(), nullable=False),
        sa.Column("cefr_level", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_generated_exercises_user_id", "generated_exercises", ["user_id"])
    op.create_index("ix_generated_exercises_content_hash", "generated_exercises", ["content_hash"])


def downgrade():
    for table in [
        "generated_exercises", "audit_logs", "provider_usage", "experiment_enrollments",
        "experiments", "researcher_invitations", "one_time_tokens", "refresh_sessions",
        "ai_jobs", "listening_attempts", "skill_mastery",
    ]:
        op.drop_table(table)
    op.drop_column("users", "placement_score")
    op.drop_column("users", "cefr_level")
    op.drop_column("users", "token_version")
    op.drop_column("users", "email_verified")
