"""Validate the migration graph without connecting to a database."""

import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def main() -> int:
    config_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1] / "backend/alembic.ini"
    )
    heads = ScriptDirectory.from_config(Config(str(config_path))).get_heads()
    print(f"Alembic heads ({len(heads)}): {', '.join(heads) or '(none)'}")
    if len(heads) != 1:
        print(f"Expected exactly one Alembic head; found {len(heads)}.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
