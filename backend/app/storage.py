"""Small S3-compatible storage adapter for Cloudflare R2 media objects."""

from functools import lru_cache

import boto3
from botocore.config import Config

from .config import Settings, get_settings


class StorageUnavailable(RuntimeError):
    """Raised when configured object storage cannot be reached or used."""


class R2Storage:
    def __init__(self, settings: Settings, client=None):
        self.settings = settings
        self._client = client

    @property
    def configured(self) -> bool:
        return any(
            (
                self.settings.r2_endpoint_url,
                self.settings.r2_bucket_name,
                self.settings.r2_access_key_id,
                self.settings.r2_secret_access_key,
            )
        )

    @property
    def enabled(self) -> bool:
        return all(
            (
                self.settings.r2_endpoint_url,
                self.settings.r2_bucket_name,
                self.settings.r2_access_key_id,
                self.settings.r2_secret_access_key,
            )
        )

    @property
    def client(self):
        if not self.enabled:
            raise StorageUnavailable("R2 storage is not configured")
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.settings.r2_endpoint_url,
                aws_access_key_id=self.settings.r2_access_key_id,
                aws_secret_access_key=self.settings.r2_secret_access_key,
                region_name="auto",
                config=Config(
                    connect_timeout=3,
                    read_timeout=10,
                    retries={"mode": "standard", "total_max_attempts": 2},
                ),
            )
        return self._client

    def put(self, key: str, data: bytes, content_type: str) -> None:
        try:
            self.client.put_object(
                Bucket=self.settings.r2_bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        except Exception as error:
            raise StorageUnavailable("R2 upload failed") from error

    def get(self, key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.settings.r2_bucket_name, Key=key)
            body = response["Body"]
            try:
                return body.read()
            finally:
                body.close()
        except Exception as error:
            raise StorageUnavailable("R2 read failed") from error

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.settings.r2_bucket_name, Key=key)
        except Exception as error:
            raise StorageUnavailable("R2 delete failed") from error


@lru_cache
def get_storage() -> R2Storage:
    return R2Storage(get_settings())
