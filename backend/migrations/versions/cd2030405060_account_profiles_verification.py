"""Account profiles and explicit email verification; retain existing accounts."""

import sqlalchemy as sa
from alembic import op

revision = "cd2030405060"
down_revision = "ab1020304050"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("first_name", sa.String(80), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(80), nullable=True))
    op.add_column("users", sa.Column("age_at_registration", sa.Integer(), nullable=True))
    op.add_column(
        "users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_check_constraint("user_age", "users", "age_at_registration BETWEEN 1 AND 120")


def downgrade():
    op.drop_constraint("user_age", "users", type_="check")
    for name in ("email_verified_at", "age_at_registration", "last_name", "first_name"):
        op.drop_column("users", name)
