import logging
from typing import Optional

import pandas as pd
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import execute_values

from app.config import settings

logger = logging.getLogger(__name__)

# Các cột cần lấy từ CSV gốc Home Credit bureau.csv, map đúng tên cột trong bảng raw.bureau
_COLUMNS = [
    "SK_ID_BUREAU",
    "SK_ID_CURR",
    "CREDIT_ACTIVE",
    "CREDIT_CURRENCY",
    "DAYS_CREDIT",
    "AMT_CREDIT_SUM",
    "AMT_CREDIT_SUM_DEBT",
]

_INSERT_SQL = """
    INSERT INTO raw.bureau (
        sk_id_bureau, sk_id_curr, credit_active, credit_currency,
        days_credit, amt_credit_sum, amt_credit_sum_debt
    ) VALUES %s
    ON CONFLICT (sk_id_bureau) DO NOTHING
"""


def seed_bureau(conn: PgConnection, csv_path: Optional[str] = None, batch_size: int = 5000) -> int:
    """
    Đọc toàn bộ bureau.csv và insert 1 lần vào raw.bureau.

    QUAN TRỌNG: raw.bureau.sk_id_curr có FOREIGN KEY tới raw.application.sk_id_curr,
    nên hàm này PHẢI được gọi SAU khi seed_application() đã insert xong toàn bộ
    raw.application — nếu không, các dòng bureau có sk_id_curr chưa tồn tại sẽ bị
    Postgres từ chối insert (vi phạm FK constraint), không phải lỗi "skip âm thầm".

    Những dòng có sk_id_curr không tồn tại trong raw.application (vd: do dataset
    bureau.csv tham chiếu sang application_test.csv mà ta không nạp) sẽ được lọc bỏ
    trước khi insert, để tránh job dừng giữa đường vì lỗi FK.
    """
    path = csv_path or settings.BUREAU_CSV_PATH
    df = pd.read_csv(path, usecols=_COLUMNS)
    df = df.dropna(subset=["SK_ID_BUREAU", "SK_ID_CURR"])

    valid_sk_id_curr = _get_existing_sk_id_curr(conn)
    before = len(df)
    df = df[df["SK_ID_CURR"].astype(int).isin(valid_sk_id_curr)]
    skipped = before - len(df)
    if skipped > 0:
        logger.warning(
            "Skipped %s/%s bureau rows: sk_id_curr not found in raw.application", skipped, before
        )

    rows = [
        (
            int(row["SK_ID_BUREAU"]),
            int(row["SK_ID_CURR"]),
            row.get("CREDIT_ACTIVE"),
            row.get("CREDIT_CURRENCY"),
            _safe_int(row.get("DAYS_CREDIT")),
            _none_if_nan(row.get("AMT_CREDIT_SUM")),
            _none_if_nan(row.get("AMT_CREDIT_SUM_DEBT")),
        )
        for _, row in df.iterrows()
    ]

    total_inserted = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            execute_values(cur, _INSERT_SQL, batch)
            conn.commit()
            total_inserted += len(batch)
            logger.info("Inserted %s/%s rows into raw.bureau", total_inserted, len(rows))

    return total_inserted


def _get_existing_sk_id_curr(conn: PgConnection) -> set:
    with conn.cursor() as cur:
        cur.execute("SELECT sk_id_curr FROM raw.application")
        return {row[0] for row in cur.fetchall()}


def _safe_int(value) -> Optional[int]:
    if value is None or pd.isna(value):
        return None
    return int(value)


def _none_if_nan(value):
    if value is None or pd.isna(value):
        return None
    return float(value)
