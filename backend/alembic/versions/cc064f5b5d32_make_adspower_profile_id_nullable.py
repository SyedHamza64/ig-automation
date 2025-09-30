"""make_adspower_profile_id_nullable

Revision ID: cc064f5b5d32
Revises: 08052b84f4b2
Create Date: 2025-09-26 20:44:57.974677

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc064f5b5d32'
down_revision: Union[str, Sequence[str], None] = '08052b84f4b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make adspower_profile_id nullable
    op.alter_column('profiles', 'adspower_profile_id', existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert adspower_profile_id to not nullable
    op.alter_column('profiles', 'adspower_profile_id', existing_type=sa.String(), nullable=False)
