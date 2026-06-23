"""
Backfill lịch sử tỷ giá USD/VND -> MinIO raw layer.
Chạy 1 lần (thủ công) để lấp đầy dữ liệu quá khứ, vd: toàn bộ khoảng thời gian
mà backend_simulator gán cho application_date (lookback N năm gần nhất).

Khác với fetch_fx_rate.py (chạy daily, 1 dòng/lần), file này gọi 1 lần duy nhất
lấy cả khoảng ngày, ghi thành 1 file Parquet chứa nhiều dòng.
"""

import argparse
from datetime import date, datetime, timedelta

import pandas as pd

from extract_jobs.config import settings
from extract_jobs.macro_extract.client.frankfurter_client import fetch_rate_range
from extract_jobs.utils.logging_config import setup_logging
from extract_jobs.utils.minio_client import ensure_bucket, get_minio_client, upload_dataframe_as_parquet

logger = setup_logging("backfill_fx_rate")


def run(start_date: date, end_date: date):
    logger.info("Backfilling USD/VND rate from %s to %s", start_date, end_date)

    rates = fetch_rate_range(start_date, end_date)
    if not rates:
        logger.warning("No rates returned for the given range.")
        return

    df = pd.DataFrame(
        [{"rate_date": d, "usd_vnd": rate} for d, rate in rates.items() if rate is not None]
    )
    df["fetched_at"] = datetime.utcnow().isoformat()
    df = df.sort_values("rate_date")

    run_timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    object_path = f"fx_rate/backfill/part-{run_timestamp}.parquet"

    client = get_minio_client()
    ensure_bucket(client, settings.MINIO_RAW_BUCKET)
    upload_dataframe_as_parquet(client, settings.MINIO_RAW_BUCKET, object_path, df)

    logger.info("Backfill complete: %s rows -> %s", len(df), object_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill USD/VND fx rate history")
    parser.add_argument("--start", type=str, help="Start date YYYY-MM-DD", default=None)
    parser.add_argument("--end", type=str, help="End date YYYY-MM-DD", default=None)
    args = parser.parse_args()

    end = date.fromisoformat(args.end) if args.end else date.today()
    start = date.fromisoformat(args.start) if args.start else end - timedelta(days=365 * 3)

    run(start, end)