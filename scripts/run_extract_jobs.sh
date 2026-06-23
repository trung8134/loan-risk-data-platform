#!/bin/bash
# Chạy thủ công các extract job (Postgres -> MinIO, API -> MinIO).
# Dùng để test trước khi Airflow đảm nhận lịch chạy tự động.

set -e

echo "=== Extracting raw.application -> MinIO ==="
docker compose run --rm postgres_extract python -m extract_jobs.postgres_extract.extract_application

echo "=== Extracting raw.bureau -> MinIO ==="
docker compose run --rm postgres_extract python -m extract_jobs.postgres_extract.extract_bureau

echo "=== Extracting FX rate (macro) -> MinIO ==="
docker compose run --rm macro_extract python -m extract_jobs.macro_extract.flows.fetch_fx_rate

echo "Done."
