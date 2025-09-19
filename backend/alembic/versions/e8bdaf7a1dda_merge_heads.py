"""merge heads

Revision ID: e8bdaf7a1dda
Revises: 9de9d45f67e, 557ea96527b6
Create Date: 2025-09-09 14:22:45.579848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8bdaf7a1dda'
down_revision: Union[str, Sequence[str], None] = ('9de9d45f67e', '557ea96527b6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
