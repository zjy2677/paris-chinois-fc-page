"""Add alternate player positions and uploaded photos."""

import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "squad_memberships",
        sa.Column("alternate_positions", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.create_table(
        "player_photos",
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("player_id"),
    )


def downgrade():
    op.drop_table("player_photos")
    op.drop_column("squad_memberships", "alternate_positions")
