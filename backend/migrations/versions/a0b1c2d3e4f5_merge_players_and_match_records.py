"""Merge player management and lightweight match record heads.

Revision ID: a0b1c2d3e4f5
Revises: b7c8d9e0f123, ef4050607080
"""

from collections.abc import Sequence

revision: str = "a0b1c2d3e4f5"
down_revision: str | Sequence[str] | None = ("b7c8d9e0f123", "ef4050607080")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
