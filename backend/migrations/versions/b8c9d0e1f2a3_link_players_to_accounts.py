"""Link each player profile to at most one registered account."""

import sqlalchemy as sa
from alembic import op

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("players", sa.Column("account_user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_players_account_user_id",
        "players",
        "users",
        ["account_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint("uq_players_account_user_id", "players", ["account_user_id"])


def downgrade():
    op.drop_constraint("uq_players_account_user_id", "players", type_="unique")
    op.drop_constraint("fk_players_account_user_id", "players", type_="foreignkey")
    op.drop_column("players", "account_user_id")
