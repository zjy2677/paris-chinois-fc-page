"""Add editable album backgrounds and slideshow settings."""

import sqlalchemy as sa
from alembic import op

revision = "f7a8b9c0d1e2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "photo_albums",
        sa.Column("background_enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "photo_albums",
        sa.Column("background_interval_seconds", sa.Integer(), server_default="8", nullable=False),
    )
    op.add_column(
        "photo_albums",
        sa.Column("background_transition", sa.String(12), server_default="fade", nullable=False),
    )
    op.add_column(
        "photo_albums",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "photo_album_background_interval",
        "photo_albums",
        "background_interval_seconds BETWEEN 3 AND 30",
    )
    op.create_check_constraint(
        "photo_album_background_transition",
        "photo_albums",
        "background_transition IN ('fade','slide','zoom')",
    )
    op.create_index(
        "uq_photo_albums_single_background",
        "photo_albums",
        ["background_enabled"],
        unique=True,
        postgresql_where=sa.text("background_enabled IS TRUE"),
        sqlite_where=sa.text("background_enabled = 1"),
    )
    op.add_column(
        "album_photos",
        sa.Column("use_as_background", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_album_photos_media_id", "album_photos", ["media_id"])


def downgrade():
    op.drop_index("ix_album_photos_media_id", table_name="album_photos")
    op.drop_column("album_photos", "use_as_background")
    op.drop_index("uq_photo_albums_single_background", table_name="photo_albums")
    op.drop_constraint("photo_album_background_transition", "photo_albums", type_="check")
    op.drop_constraint("photo_album_background_interval", "photo_albums", type_="check")
    op.drop_column("photo_albums", "updated_at")
    op.drop_column("photo_albums", "background_transition")
    op.drop_column("photo_albums", "background_interval_seconds")
    op.drop_column("photo_albums", "background_enabled")
