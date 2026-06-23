"""
Extract tỷ giá USD/VND mới nhất từ frankfurter.app -> MinIO raw layer (Parquet).

Chạy theo lịch hàng ngày (Airflow). Mỗi lần chạy, lấy tỷ giá mới nhất hiện có,
ghi thành 1 file Parquet nhỏ (1 dòng), upload vào:
    raw/fx_rate/extract_date=YYYY-MM-DD/part-<timestamp>.parquet

Không cần checkpoint phức tạp như postgres_extract vì đây là API trả "giá trị
hiện tại", không phải bảng có updated_at để so sánh.
"""

from datetime import datetime

import pandas as pd

from extract_jobs.config import settings
from extract_jobs.macro_extract.client.frankfurter_client import fetch_latest_rate
from extract_jobs.utils.logging_config import setup_logging
from extract_jobs.utils.minio_client import ensure_bucket, get_minio_client, upload_dataframe_as_parquet

logger = setup_logging("fetch_fx_rate")


def run():
    rate_date, rate = fetch_latest_rate()
    logger.info("Fetched USD/VND rate: %s on %s", rate, rate_date)

    df = pd.DataFrame([{
        "rate_date": rate_date.isoformat(),
        "usd_vnd": rate,
        "fetched_at": datetime.utcnow().isoformat(),
    }])

    extract_date = datetime.utcnow().strftime("%Y-%m-%d")
    run_timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    object_path = f"fx_rate/extract_date={extract_date}/part-{run_timestamp}.parquet"

    client = get_minio_client()
    ensure_bucket(client, settings.MINIO_RAW_BUCKET)
    upload_dataframe_as_parquet(client, settings.MINIO_RAW_BUCKET, object_path, df)

    logger.info("Upload complete: %s", object_path)


if __name__ == "__main__":
    run()