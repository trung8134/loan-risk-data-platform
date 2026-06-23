import logging
import os
from pathlib import Path


def setup_logging(job_name: str) -> logging.Logger:
    """
    Cấu hình logging chung cho 1 job: vừa in ra console (để xem trực tiếp qua
    `docker compose logs`), vừa ghi vào file persistent dưới /app/logs/ (mount
    ra ngoài host qua volume, không mất khi container bị xóa).

    File log đặt tên theo job_name, append dần qua các lần chạy — giúp xem lại
    lịch sử chạy khi Airflow trigger job này theo lịch tự động.
    """
    log_dir = Path(os.getenv("LOG_DIR", "/app/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{job_name}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    return logging.getLogger(job_name)