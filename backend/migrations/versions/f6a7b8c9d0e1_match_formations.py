"""Persist match tactical board placements."""

import sqlalchemy as sa
from alembic import op

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "formation_placements",
        sa.Column(
            "match_id", sa.Uuid(), sa.ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column(
            "player_id",
            sa.Uuid(),
            sa.ForeignKey("players.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("placement", sa.String(10), nullable=False),
        sa.Column("x", sa.Float(), nullable=True),
        sa.Column("y", sa.Float(), nullable=True),
        sa.CheckConstraint("placement IN ('pitch','bench')", name="formation_placement"),
        sa.CheckConstraint(
            "(placement = 'bench' AND x IS NULL AND y IS NULL) OR "
            "(placement = 'pitch' AND x IS NOT NULL AND y IS NOT NULL "
            "AND x BETWEEN 0 AND 100 AND y BETWEEN 0 AND 100)",
            name="formation_coordinates",
        ),
    )


def downgrade():
    op.drop_table("formation_placements")
