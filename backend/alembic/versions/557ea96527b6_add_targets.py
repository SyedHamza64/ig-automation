from alembic import op

revision = "557ea96527b6"
down_revision = "71110fa2c8ff"
branch_labels = None
depends_on = None

def upgrade():
    # This migration duplicated 'add targets'. Make it a no-op.
    pass

def downgrade():
    # No-op
    pass
