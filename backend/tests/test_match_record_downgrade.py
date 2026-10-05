"""Check the rollback guard without dropping tables in a shared test database."""

import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.mark.parametrize("has_manual_data", [True, False])
def test_manual_records_downgrade_guard(monkeypatch, has_manual_data):
    path = Path(__file__).parents[1] / "migrations/versions/ef4050607080_match_records.py"
    spec = importlib.util.spec_from_file_location("match_records_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    operations = Mock()
    operations.get_bind.return_value.execute.return_value.scalar_one.return_value = has_manual_data
    monkeypatch.setattr(migration, "op", operations)
    if has_manual_data:
        with pytest.raises(RuntimeError, match="Export and reconcile manual data"):
            migration.downgrade()
        operations.drop_table.assert_not_called()
        operations.drop_column.assert_not_called()
        operations.alter_column.assert_not_called()
    else:
        migration.downgrade()
        assert operations.drop_table.call_count == 2
        operations.alter_column.assert_called_once()
