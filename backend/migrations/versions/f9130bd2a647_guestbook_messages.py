"""Add the public guestbook wall."""

import sqlalchemy as sa
from alembic import op

revision = "f9130bd2a647"
down_revision = "e84a76c1d905"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "guestbook_messages",
        sa.Column("nickname", sa.String(length=30), nullable=False),
        sa.Column("body", sa.String(length=300), nullable=False),
        sa.Column("visitor_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="visible", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("status IN ('visible','hidden')", name="guestbook_message_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_guestbook_status_created", "guestbook_messages", ["status", "created_at"])
    op.create_index("ix_guestbook_messages_visitor_hash", "guestbook_messages", ["visitor_hash"])


def downgrade():
    op.drop_index("ix_guestbook_messages_visitor_hash", table_name="guestbook_messages")
    op.drop_index("ix_guestbook_status_created", table_name="guestbook_messages")
    op.drop_table("guestbook_messages")
