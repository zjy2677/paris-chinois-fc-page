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
    # Check every table before changing any columns; also works with --sql.
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM user_avatars WHERE data IS NULL)
                OR EXISTS (SELECT 1 FROM player_photos WHERE data IS NULL)
                OR EXISTS (SELECT 1 FROM media_assets WHERE data IS NULL)
            THEN
                RAISE EXCEPTION 'Cannot downgrade R2 storage: restore all photo data bytes from R2 first. See backend/README.md, R2 rollback.';
            END IF;
        END $$;
    """)
    for table in ("user_avatars", "player_photos", "media_assets"):
        op.alter_column(
            table,
            "data",
            existing_type=sa.LargeBinary(),
            nullable=False,
        )
        op.drop_constraint(f"uq_{table}_storage_key", table, type_="unique")
        op.drop_column(table, "storage_key")
