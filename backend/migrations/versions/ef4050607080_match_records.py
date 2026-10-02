"""Add lightweight match records and manual matches.

Revision ID: ef4050607080
Revises: 1a2b3c4d5e6f
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "ef4050607080"
down_revision: str | Sequence[str] | None = "1a2b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("teams", "fla_team_id", existing_type=sa.Integer(), nullable=True)
    op.drop_constraint("one_competition_source", "competition_seasons", type_="check")
    op.create_check_constraint(
        "one_competition_source",
        "competition_seasons",
        "NOT (fla_championship_id IS NOT NULL AND fla_cup_id IS NOT NULL)",
    )
    op.add_column(
        "matches",
        sa.Column("source_type", sa.String(20), server_default="synced", nullable=False),
    )
    op.create_check_constraint(
        "match_source_type", "matches", "source_type IN ('synced','manual')"
    )
    op.create_table(
        "match_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_id"),
    )
    op.create_index("ix_match_reports_match_id", "match_reports", ["match_id"])
    op.create_table(
        "match_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("assist_player_id", sa.Uuid(), nullable=True),
        sa.Column("minute", sa.Integer(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.CheckConstraint("event_type IN ('goal','yellow_card','red_card')", name="event_type"),
        sa.CheckConstraint("minute IS NULL OR minute BETWEEN 0 AND 130", name="event_minute"),
        sa.CheckConstraint("event_type = 'goal' OR assist_player_id IS NULL", name="assist_only_for_goal"),
        sa.CheckConstraint("player_id <> assist_player_id", name="scorer_not_assistant"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assist_player_id"], ["players.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_match_events_match_sequence", "match_events", ["match_id", "sequence"])


def downgrade() -> None:
    op.drop_table("match_events")
    op.drop_table("match_reports")
    op.drop_constraint("match_source_type", "matches", type_="check")
    op.drop_column("matches", "source_type")
    op.drop_constraint("one_competition_source", "competition_seasons", type_="check")
    op.create_check_constraint(
        "one_competition_source",
        "competition_seasons",
        "(fla_championship_id IS NULL) <> (fla_cup_id IS NULL)",
    )
    op.alter_column("teams", "fla_team_id", existing_type=sa.Integer(), nullable=False)
