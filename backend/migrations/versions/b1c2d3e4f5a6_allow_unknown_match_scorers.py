"""Allow an unknown scorer in lightweight match goal events.

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "a0b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("match_events", "player_id", existing_type=sa.Uuid(), nullable=True)


def downgrade() -> None:
    op.alter_column("match_events", "player_id", existing_type=sa.Uuid(), nullable=False)
