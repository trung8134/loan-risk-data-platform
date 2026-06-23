import logging
import os
from pathlib import Path


def setup_logging(job_name: str) -> logging.Logger:
    """
    Cấu hình logging chung: in ra console + ghi file persistent dưới /app/logs/
    (mount ra ngoài host qua volume, không mất khi container bị xóa sau khi
    chạy xong, vd: docker compose run --rm).
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