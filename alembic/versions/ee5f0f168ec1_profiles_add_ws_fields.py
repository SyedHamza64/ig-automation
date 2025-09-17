"""profiles: add ws fields

Revision ID: ee5f0f168ec1
Revises: 18e8854992e4
Create Date: 2025-09-10 15:57:11.093129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee5f0f168ec1'
down_revision: Union[str, Sequence[str], None] = '18e8854992e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Use raw SQL for idempotency on Postgres
    op.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS last_ws_puppeteer TEXT;")
    op.execute("ALTER TABLE profiles ADD COLUMN IF NOT EXISTS last_ws_selenium  TEXT;")

def downgrade():
    op.execute("ALTER TABLE profiles DROP COLUMN IF EXISTS last_ws_selenium;")
    op.execute("ALTER TABLE profiles DROP COLUMN IF EXISTS last_ws_puppeteer;")
