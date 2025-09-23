"""Make profiles.account_id nullable and enforce 1:1 + unique adspower id

Revision ID: 53ac0426c080
Revises: 0429874dcc29
Create Date: 2025-09-20 01:46:48.774303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53ac0426c080'
down_revision: Union[str, Sequence[str], None] = '0429874dcc29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Make account_id nullable
    op.alter_column("profiles", "account_id",
                    existing_type=sa.Integer(),
                    nullable=True)

    # 2) Ensure adspower_profile_id is globally unique
    # (drop if an old constraint exists with a different name)
    try:
        op.create_unique_constraint(
            "uq_profiles_adspower_profile_id",
            "profiles",
            ["adspower_profile_id"],
        )
    except Exception:
        pass

    # 3) Enforce 1:1 only when linked: unique where account_id is NOT NULL
    # (partial unique index — Postgres)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_profiles_one_per_account
        ON profiles (account_id)
        WHERE account_id IS NOT NULL;
    """)

def downgrade():
    # Drop the partial index
    op.execute("DROP INDEX IF EXISTS ux_profiles_one_per_account;")

    # Drop unique on adspower id
    try:
        op.drop_constraint("uq_profiles_adspower_profile_id", "profiles", type_="unique")
    except Exception:
        pass

    # Make account_id NOT NULL again (will fail if NULL rows exist)
    op.alter_column("profiles", "account_id",
                    existing_type=sa.Integer(),
                    nullable=False)