from alembic import op

revision = "9de9d45f67e"
down_revision = "71110fa2c8ff"  # important to point to the add_targets branchpoint
branch_labels = None
depends_on = None

def upgrade():
    op.execute("ALTER TABLE targets ALTER COLUMN labels TYPE jsonb USING labels::jsonb;")

def downgrade():
    op.execute("ALTER TABLE targets ALTER COLUMN labels TYPE json USING labels::json;")
