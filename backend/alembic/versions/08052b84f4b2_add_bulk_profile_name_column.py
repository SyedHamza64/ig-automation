"""add_bulk_profile_name_column

Revision ID: 08052b84f4b2
Revises: 53ac0426c080
Create Date: 2025-09-26 20:43:10.696910

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08052b84f4b2'
down_revision: Union[str, Sequence[str], None] = '53ac0426c080'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add bulk_profile_name column
    op.add_column('profiles', sa.Column('bulk_profile_name', sa.String(), nullable=True))
    op.create_index(op.f('ix_profiles_bulk_profile_name'), 'profiles', ['bulk_profile_name'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove bulk_profile_name column
    op.drop_index(op.f('ix_profiles_bulk_profile_name'), table_name='profiles')
    op.drop_column('profiles', 'bulk_profile_name')
