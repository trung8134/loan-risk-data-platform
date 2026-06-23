import io
import logging

import pandas as pd
from minio import Minio
from minio.error import S3Error

from extract_jobs.config import settings

logger = logging.getLogger(__name__)


def get_minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def ensure_bucket(client: Minio, bucket_name: str) -> None:
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        logger.info("Created MinIO bucket: %s", bucket_name)


def upload_dataframe_as_parquet(
    client: Minio,
    bucket_name: str,
    object_path: str,
    df: pd.DataFrame,
) -> None:
    """
    Ghi DataFrame thành Parquet trong memory rồi upload thẳng lên MinIO,
    không cần tạo file tạm trên đĩa container.
    """
    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)
    size = buffer.getbuffer().nbytes

    try:
        client.put_object(
            bucket_name=bucket_name,
            object_name=object_path,
            data=buffer,
            length=size,
            content_type="application/octet-stream",
        )
        logger.info("Uploaded %s rows to s3://%s/%s", len(df), bucket_name, object_path)
    except S3Error as e:
        logger.error("Failed to upload to MinIO: %s", e)
        raise
