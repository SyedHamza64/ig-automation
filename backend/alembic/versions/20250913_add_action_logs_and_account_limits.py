"""add action_logs and account_limits

Revision ID: 20250913_action_phase4
Revises: e8bdaf7a1dda_merge_heads
Create Date: 2025-09-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "20250913_action_phase4"
down_revision = "e8bdaf7a1dda" 
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "account_limits",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("limits_json", pg.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "action_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("profile_id", sa.Integer, sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("action_type", sa.String(32), nullable=False, index=True),
        sa.Column("payload", pg.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(32), nullable=False, index=True),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )

    op.create_index("ix_action_logs_account_created_at", "action_logs", ["account_id", "created_at"])
    op.create_index("ix_action_logs_actiontype_created_at", "action_logs", ["action_type", "created_at"])


def downgrade():
    op.drop_index("ix_action_logs_actiontype_created_at", table_name="action_logs")
    op.drop_index("ix_action_logs_account_created_at", table_name="action_logs")
    op.drop_table("action_logs")
    op.drop_table("account_limits")
