"""Require exactly one league or cup source identifier."""

from alembic import op

revision = "e2370a810101"
down_revision = "d519dc376422"
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint(
        "one_competition_source",
        "competition_seasons",
        "(fla_championship_id IS NULL) <> (fla_cup_id IS NULL)",
    )


def downgrade():
    op.drop_constraint("one_competition_source", "competition_seasons", type_="check")
