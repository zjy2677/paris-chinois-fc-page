"""Retain object deletions for retry after committing photo changes."""

import sqlalchemy as sa
from alembic import op

revision = "c5d6e7f8a9b0"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "storage_deletions",
        sa.Column("storage_key", sa.String(512), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade():
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM storage_deletions) THEN
                RAISE EXCEPTION 'Cannot remove pending R2 deletions: run python -m app.photo_storage first.';
            END IF;
        END $$;
    """)
    op.drop_table("storage_deletions")
