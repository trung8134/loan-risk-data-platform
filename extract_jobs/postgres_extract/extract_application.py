"""
Extract incremental từ raw.application (Postgres) -> MinIO raw layer (Parquet).

Logic:
1. Đọc checkpoint (last_extracted_at) từ raw.etl_checkpoint cho bảng 'raw.application'.
2. Query: SELECT * FROM raw.application WHERE updated_at > :checkpoint ORDER BY updated_at
3. Nếu có dòng mới -> ghi thành 1 file Parquet, partition theo ngày extract (YYYY-MM-DD),
   upload lên MinIO bucket 'raw', path: application/extract_date=YYYY-MM-DD/part-<timestamp>.parquet
4. Cập nhật checkpoint = MAX(updated_at) của batch vừa lấy được.

Chạy độc lập (không phụ thuộc Spark) — Airflow sẽ schedule job này theo lịch.
"""

from datetime import datetime
import pandas as pd

from extract_jobs.config import settings
from extract_jobs.utils.checkpoint import get_last_checkpoint, get_postgres_connection, update_checkpoint
from extract_jobs.utils.logging_config import setup_logging
from extract_jobs.utils.minio_client import ensure_bucket, get_minio_client, upload_dataframe_as_parquet

logger = setup_logging("extract_application")


SOURCE_TABLE = "raw.application"
EXTRACT_QUERY = """
    SELECT
        sk_id_curr, target, name_contract_type, code_gender, flag_own_car,
        flag_own_realty, cnt_children, amt_income_total, amt_credit, amt_annuity,
        amt_goods_price, name_income_type, name_education_type, name_family_status,
        name_housing_type, days_birth, days_employed, application_date,
        created_at, updated_at
    FROM raw.application
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
        object_path = f"application/extract_date={extract_date}/part-{run_timestamp}.parquet"

        client = get_minio_client()
        ensure_bucket(client, settings.MINIO_RAW_BUCKET)
        upload_dataframe_as_parquet(client, settings.MINIO_RAW_BUCKET, object_path, df)

        update_checkpoint(conn, SOURCE_TABLE, new_checkpoint, len(df))

        logger.info("Extract complete: %s rows -> %s", len(df), object_path)
    finally:
        conn.close()


if __name__ == "__main__":
    run()