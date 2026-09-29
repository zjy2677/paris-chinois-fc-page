"""Add anonymous homepage likes."""

import sqlalchemy as sa
from alembic import op

revision = "c42f083b219a"
down_revision = "ab1020304050"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "homepage_likes",
        sa.Column("visitor_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("visitor_hash", name="uq_homepage_like_visitor"),
    )


def downgrade():
    op.drop_table("homepage_likes")
