"""Add a public player description."""

import sqlalchemy as sa
from alembic import op

revision = "b7c8d9e0f123"
down_revision = "f0ad5f64a5bd"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("players", sa.Column("description", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("players", "description")
