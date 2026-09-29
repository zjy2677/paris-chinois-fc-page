"""Remove the redundant blog summary."""

import sqlalchemy as sa
from alembic import op

revision = "e84a76c1d905"
down_revision = "d71e5c0a4b32"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("blog_posts", "summary")


def downgrade():
    op.add_column(
        "blog_posts",
        sa.Column("summary", sa.String(length=320), server_default="", nullable=False),
    )
    op.alter_column("blog_posts", "summary", server_default=None)
