"""Add one five-star review per account, player, and match."""

import sqlalchemy as sa
from alembic import op

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "match_player_ratings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "match_id", sa.Uuid(), sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "player_id", sa.Uuid(), sa.ForeignKey("players.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("match_id", "player_id", "user_id", name="uq_match_player_rater"),
        sa.CheckConstraint("stars BETWEEN 1 AND 5", name="match_player_rating_stars"),
    )
    op.create_index(
        "ix_match_player_ratings_player", "match_player_ratings", ["match_id", "player_id"]
    )


def downgrade():
    op.drop_index("ix_match_player_ratings_player", table_name="match_player_ratings")
    op.drop_table("match_player_ratings")
