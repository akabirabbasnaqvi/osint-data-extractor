"""create jobs and results tables

Revision ID: 0001
Revises:
Create Date: 2026-07-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("inputs", postgresql.JSONB, nullable=False),
        sa.Column("retrieve", postgresql.ARRAY(sa.String), nullable=False),
        sa.Column("progress", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_msg", sa.Text, nullable=True),
    )

    op.create_table(
        "results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("data", postgresql.JSONB, nullable=False),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("idx_results_job_id", "results", ["job_id"])
    op.create_index("idx_jobs_session", "jobs", ["session_id"])


def downgrade() -> None:
    op.drop_index("idx_jobs_session", table_name="jobs")
    op.drop_index("idx_results_job_id", table_name="results")
    op.drop_table("results")
    op.drop_table("jobs")
