import logging
import random
from datetime import date, timedelta
from typing import Optional

import pandas as pd
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import execute_values

from app.config import settings

logger = logging.getLogger(__name__)

# Số năm lùi lại tính từ hôm nay để random application_date — tạo dữ liệu thời gian
# đa dạng cho Spark join với raw.fx_rate_daily (macro data) ở bước transform sau này.
_LOOKBACK_YEARS = 3

# Các cột cần lấy từ CSV gốc Home Credit, map đúng tên cột trong bảng raw.application
_COLUMNS = [
    "SK_ID_CURR",
    "TARGET",
    "NAME_CONTRACT_TYPE",
    "CODE_GENDER",
    "FLAG_OWN_CAR",
    "FLAG_OWN_REALTY",
    "CNT_CHILDREN",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "NAME_INCOME_TYPE",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "NAME_HOUSING_TYPE",
    "DAYS_BIRTH",
    "DAYS_EMPLOYED",
]

_INSERT_SQL = """
    INSERT INTO raw.application (
        sk_id_curr, target, name_contract_type, code_gender, flag_own_car,
        flag_own_realty, cnt_children, amt_income_total, amt_credit, amt_annuity,
        amt_goods_price, name_income_type, name_education_type, name_family_status,
        name_housing_type, days_birth, days_employed, application_date
    ) VALUES %s
    ON CONFLICT (sk_id_curr) DO NOTHING
"""


def _random_application_date() -> date:
    """Random 1 ngày trong khoảng [hôm nay - LOOKBACK_YEARS năm, hôm nay]."""
    today = date.today()
    earliest = today - timedelta(days=365 * _LOOKBACK_YEARS)
    delta_days = (today - earliest).days
    return earliest + timedelta(days=random.randint(0, delta_days))


def seed_application(conn: PgConnection, csv_path: Optional[str] = None, batch_size: int = 5000) -> int:
    """
    Đọc toàn bộ Home Credit application CSV và insert 1 lần vào raw.application.
    Mỗi dòng được gán application_date ngẫu nhiên trong _LOOKBACK_YEARS năm gần nhất,
    để dataset có sự phân bố theo thời gian thực tế khi join với macro data (fx_rate)
    ở bước Spark transform sau này — tránh việc toàn bộ dòng cùng 1 ngày insert.

    Dùng execute_values để bulk insert theo batch (nhanh hơn nhiều so với insert từng dòng
    khi dataset có ~300k dòng). Trả về tổng số dòng đã insert thành công.
    """
    path = csv_path or settings.APPLICATION_CSV_PATH
    df = pd.read_csv(path, usecols=_COLUMNS)
    df = df.dropna(subset=["SK_ID_CURR"])

    rows = [
        (
            int(row["SK_ID_CURR"]),
            _safe_int(row.get("TARGET")),
            row.get("NAME_CONTRACT_TYPE"),
            row.get("CODE_GENDER"),
            row.get("FLAG_OWN_CAR"),
            row.get("FLAG_OWN_REALTY"),
            _safe_int(row.get("CNT_CHILDREN")),
            _none_if_nan(row.get("AMT_INCOME_TOTAL")),
            _none_if_nan(row.get("AMT_CREDIT")),
            _none_if_nan(row.get("AMT_ANNUITY")),
            _none_if_nan(row.get("AMT_GOODS_PRICE")),
            row.get("NAME_INCOME_TYPE"),
            row.get("NAME_EDUCATION_TYPE"),
            row.get("NAME_FAMILY_STATUS"),
            row.get("NAME_HOUSING_TYPE"),
            _safe_int(row.get("DAYS_BIRTH")),
            _safe_int(row.get("DAYS_EMPLOYED")),
            _random_application_date(),
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
            logger.info("Inserted %s/%s rows into raw.application", total_inserted, len(rows))

    return total_inserted


def _safe_int(value) -> Optional[int]:
    if value is None or pd.isna(value):
        return None
    return int(value)


def _none_if_nan(value):
    if value is None or pd.isna(value):
        return None
    return float(value)
