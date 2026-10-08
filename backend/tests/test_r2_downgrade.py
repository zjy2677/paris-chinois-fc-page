"""Execute downgrade guards against temporary PostgreSQL tables only."""

import importlib.util
import os
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError


@pytest.mark.parametrize("missing_bytes", [None, "media_assets", "player_photos", "user_avatars"])
def test_r2_rollback_checks_all_tables_before_ddl(monkeypatch, missing_bytes):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires disposable PostgreSQL TEST_DATABASE_URL")
    engine = create_engine(url)
    assert engine.url.database.endswith("_test")
    path = Path(__file__).parents[1] / "migrations/versions/b2c3d4e5f6a7_r2_media_storage.py"
    spec = importlib.util.spec_from_file_location("r2_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                for table in ("media_assets", "player_photos", "user_avatars"):
                    connection.execute(
                        text(f"CREATE TEMP TABLE {table} (data bytea) ON COMMIT DROP")
                    )
                    connection.execute(
                        text(f"INSERT INTO {table} (data) VALUES (:data)"),
                        {"data": None if table == missing_bytes else b"photo"},
                    )
                operations = Mock()
                operations.execute.side_effect = lambda sql: connection.execute(text(sql))
                monkeypatch.setattr(migration, "op", operations)
                if missing_bytes:
                    with pytest.raises(
                        DBAPIError, match="restore all photo data bytes from R2 first"
                    ):
                        migration.downgrade()
                    operations.alter_column.assert_not_called()
                    operations.drop_column.assert_not_called()
                else:
                    migration.downgrade()
                    assert operations.alter_column.call_count == 3
                    assert operations.drop_column.call_count == 3
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
