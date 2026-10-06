"""Add Chinese player names, preserving existing display names as English names."""

import sqlalchemy as sa
from alembic import op

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    # Legacy players keep their English names until an admin provides a Chinese name.
    op.add_column("players", sa.Column("chinese_name", sa.String(length=150), nullable=True))


def downgrade():
    op.drop_column("players", "chinese_name")
