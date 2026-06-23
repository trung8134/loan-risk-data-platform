import logging
from datetime import datetime
from typing import Optional

import psycopg2

from extract_jobs.config import settings

logger = logging.getLogger(__name__)


def get_postgres_connection():
    return psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
    )


def get_last_checkpoint(conn, source_table: str) -> datetime:
    """
    Đọc last_extracted_at của source_table từ raw.etl_checkpoint.
    Nếu chưa có dòng nào (chưa từng extract), trả về epoch (1970-01-01) để job
    tự hiểu là "lấy toàn bộ" ở lần chạy đầu tiên.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT last_extracted_at FROM raw.etl_checkpoint WHERE source_table = %s",
            (source_table,),
        )
        result = cur.fetchone()
        if result is None:
            return datetime(1970, 1, 1)
        return result[0]


def update_checkpoint(conn, source_table: str, new_checkpoint: datetime, row_count: int) -> None:
    """
    Cập nhật checkpoint sau khi extract xong 1 batch thành công.
    Dùng UPSERT để vừa hoạt động cho lần đầu (chưa có dòng) vừa cho các lần sau.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw.etl_checkpoint (source_table, last_extracted_at, last_run_at, last_row_count)
            VALUES (%s, %s, now(), %s)
            ON CONFLICT (source_table) DO UPDATE SET
                last_extracted_at = EXCLUDED.last_extracted_at,
                last_run_at = EXCLUDED.last_run_at,
                last_row_count = EXCLUDED.last_row_count
            """,
            (source_table, new_checkpoint, row_count),
        )
    conn.commit()
    logger.info(
        "Checkpoint updated: table=%s new_checkpoint=%s rows=%s",
        source_table, new_checkpoint, row_count,
    )
