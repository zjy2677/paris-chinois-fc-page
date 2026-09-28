"""Limit account roles and default new accounts to user."""

import sqlalchemy as sa
from alembic import op

revision = "ab1020304050"
down_revision = "bac727c65584"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("users", "role", existing_type=sa.String(20), server_default="user")
    op.create_check_constraint("user_role", "users", "role IN ('user', 'player', 'admin')")


def downgrade():
    op.drop_constraint("user_role", "users", type_="check")
    op.alter_column("users", "role", existing_type=sa.String(20), server_default=None)
