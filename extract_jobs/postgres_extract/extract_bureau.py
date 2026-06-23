"""
Extract incremental từ raw.bureau (Postgres) -> MinIO raw layer (Parquet).
Cùng pattern với extract_application.py — xem docstring ở đó để hiểu logic chung.
"""

from datetime import datetime
import pandas as pd

from extract_jobs.config import settings
from extract_jobs.utils.checkpoint import get_last_checkpoint, get_postgres_connection, update_checkpoint
from extract_jobs.utils.logging_config import setup_logging
from extract_jobs.utils.minio_client import ensure_bucket, get_minio_client, upload_dataframe_as_parquet

logger = setup_logging("extract_bureau")

SOURCE_TABLE = "raw.bureau"
EXTRACT_QUERY = """
    SELECT
        sk_id_bureau, sk_id_curr, credit_active, credit_currency,
        days_credit, amt_credit_sum, amt_credit_sum_debt,
        created_at, updated_at
    FROM raw.bureau
    WHERE updated_at > %s
    ORDER BY updated_at
"""


def run():
    conn = get_postgres_connection()
    try:
        checkpoint = get_last_checkpoint(conn, SOURCE_TABLE)
        logger.info("Last checkpoint for %s: %s", SOURCE_TABLE, checkpoint)

        df = pd.read_sql(EXTRACT_QUERY, conn, params=(checkpoint,))

        if df.empty:
            logger.info("No new/updated rows since last checkpoint. Skipping upload.")
            return

        new_checkpoint = df["updated_at"].max()
        extract_date = datetime.utcnow().strftime("%Y-%m-%d")
        run_timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        object_path = f"bureau/extract_date={extract_date}/part-{run_timestamp}.parquet"

        client = get_minio_client()
        ensure_bucket(client, settings.MINIO_RAW_BUCKET)
        upload_dataframe_as_parquet(client, settings.MINIO_RAW_BUCKET, object_path, df)

        update_checkpoint(conn, SOURCE_TABLE, new_checkpoint, len(df))

        logger.info("Extract complete: %s rows -> %s", len(df), object_path)
    finally:
        conn.close()


if __name__ == "__main__":
    run()