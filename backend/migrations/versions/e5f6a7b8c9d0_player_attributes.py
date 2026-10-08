"""Add admin-assessed player strengths and weaknesses."""

import sqlalchemy as sa
from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "player_attributes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "player_id", sa.Uuid(), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("kind IN ('strength', 'weakness')", name="player_attribute_kind"),
        sa.CheckConstraint("level BETWEEN 1 AND 5", name="player_attribute_level"),
    )
    op.create_index("ix_player_attributes_player_id", "player_attributes", ["player_id"])


def downgrade():
    op.drop_table("player_attributes")
