"""Add shared media library and photo albums."""

import sqlalchemy as sa
from alembic import op

revision = "a4b5c6d7e8f9"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "photo_albums",
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "media_assets",
        sa.Column("uploaded_by", sa.Uuid(), nullable=True),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("caption", sa.String(300), nullable=True),
        sa.Column("alt_text", sa.String(300), server_default="", nullable=False),
        sa.Column("status", sa.String(20), server_default="visible", nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("match_id", sa.Uuid(), nullable=True),
        sa.Column("blog_post_id", sa.Uuid(), nullable=True),
        sa.Column("guestbook_message_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("size_bytes > 0", name="media_asset_size_positive"),
        sa.CheckConstraint("status IN ('visible','pending','hidden')", name="media_asset_status"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["blog_post_id"], ["blog_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["guestbook_message_id"], ["guestbook_messages.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_media_assets_uploaded_by", "media_assets", ["uploaded_by"])
    op.create_index("ix_media_match", "media_assets", ["match_id", "position"])
    op.create_index("ix_media_blog", "media_assets", ["blog_post_id", "position"])
    op.create_index("ix_media_guestbook", "media_assets", ["guestbook_message_id", "position"])
    op.create_table(
        "album_photos",
        sa.Column("album_id", sa.Uuid(), nullable=False),
        sa.Column("media_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["album_id"], ["photo_albums.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_id"], ["media_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("album_id", "media_id"),
    )


def downgrade():
    op.drop_table("album_photos")
    op.drop_index("ix_media_guestbook", table_name="media_assets")
    op.drop_index("ix_media_blog", table_name="media_assets")
    op.drop_index("ix_media_match", table_name="media_assets")
    op.drop_index("ix_media_assets_uploaded_by", table_name="media_assets")
    op.drop_table("media_assets")
    op.drop_table("photo_albums")
