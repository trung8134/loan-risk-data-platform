#!/bin/bash
# Seed 1 lần toàn bộ Home Credit CSV (application_train.csv, bureau.csv) vào Postgres.
# Chạy 1 lần duy nhất sau khi Postgres đã khởi tạo schema xong.

set -e

echo "=== Seeding raw.application + raw.bureau from CSV (1-time load) ==="
docker compose run --rm backend_simulator

echo "Done."