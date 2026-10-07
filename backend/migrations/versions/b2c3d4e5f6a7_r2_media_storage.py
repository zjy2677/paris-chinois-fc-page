"""Add optional object-storage keys for uploaded images."""

import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a4b5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("media_assets", "player_photos", "user_avatars"):
        op.add_column(table, sa.Column("storage_key", sa.String(length=512), nullable=True))
        op.create_unique_constraint(f"uq_{table}_storage_key", table, ["storage_key"])
        op.alter_column(
            table,
            "data",
            existing_type=sa.LargeBinary(),
            nullable=True,
        )


def downgrade():
    for table in ("user_avatars", "player_photos", "media_assets"):
        op.alter_column(
            table,
            "data",
            existing_type=sa.LargeBinary(),
            nullable=False,
        )
        op.drop_constraint(f"uq_{table}_storage_key", table, type_="unique")
        op.drop_column(table, "storage_key")
