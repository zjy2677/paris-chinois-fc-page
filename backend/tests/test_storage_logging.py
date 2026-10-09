"""Storage diagnostics must identify failures without exposing request contents."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from app.storage import R2Storage, StorageUnavailable
from botocore.exceptions import ClientError


@pytest.mark.parametrize("operation", ["put", "get", "delete"])
def test_storage_failure_logs_safe_metadata(operation, caplog):
    client = Mock()
    error = ClientError(
        {
            "Error": {"Code": "AccessDenied", "Message": "secret-credential"},
            "ResponseMetadata": {"HTTPStatusCode": 403},
        },
        operation,
    )
    getattr(client, f"{operation}_object").side_effect = error
    settings = SimpleNamespace(
        r2_endpoint_url="https://private-endpoint.example",
        r2_bucket_name="private-bucket",
        r2_access_key_id="secret-access-key",
        r2_secret_access_key="secret-credential",
    )
    storage = R2Storage(settings, client)
    args = (
        ("private-key", b"private-image", "image/png") if operation == "put" else ("private-key",)
    )
    with pytest.raises(StorageUnavailable):
        getattr(storage, operation)(*args)
    assert f"operation={operation}" in caplog.text
    assert "exception_type=ClientError" in caplog.text
    assert "code=AccessDenied" in caplog.text
    assert "http_status=403" in caplog.text
    for private in (
        "secret-credential",
        "secret-access-key",
        "private-image",
        "private-key",
        "private-bucket",
        "private-endpoint",
    ):
        assert private not in caplog.text
