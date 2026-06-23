import logging
from datetime import date
from typing import Optional

import requests

from extract_jobs.config import settings

logger = logging.getLogger(__name__)


def fetch_rate_on_date(target_date: date) -> Optional[float]:
    """
    Lấy tỷ giá USD -> VND tại 1 ngày cụ thể từ frankfurter.app.
    Trả về None nếu ngày đó không có dữ liệu (vd: cuối tuần, ngày lễ ECB không công bố).
    """
    date_str = target_date.strftime("%Y-%m-%d")
    url = f"{settings.FRANKFURTER_BASE_URL}/{date_str}?from=USD&to=VND"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    rate = data.get("rates", {}).get("VND")
    if rate is None:
        logger.warning("No VND rate found for %s", date_str)
        return None
    return float(rate)


def fetch_rate_range(start_date: date, end_date: date) -> dict:
    """
    Lấy tỷ giá USD -> VND cho 1 khoảng ngày (dùng cho backfill lịch sử).
    Trả về dict {date_str: rate}.
    """
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    url = f"{settings.FRANKFURTER_BASE_URL}/{start_str}..{end_str}?from=USD&to=VND"

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    rates_by_date = data.get("rates", {})
    return {d: rates.get("VND") for d, rates in rates_by_date.items() if "VND" in rates}


def fetch_latest_rate():
    """Lấy tỷ giá mới nhất hiện có (thường là ngày làm việc gần nhất). Trả về (date, rate)."""
    url = f"{settings.FRANKFURTER_BASE_URL}/latest?from=USD&to=VND"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    rate_date = date.fromisoformat(data["date"])
    rate = float(data["rates"]["VND"])
    return rate_date, rate
