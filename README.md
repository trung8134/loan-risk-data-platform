# Home Credit ELT Data Engineering Project

Mid-size ELT data engineering portfolio project using the Home Credit Default Risk dataset
(simulated as a live production database) enriched with a real macroeconomic data source
(USD/VND FX rate). Demonstrates incremental extract, a MinIO-based data lake, and Spark-based
transform/load into a Postgres data warehouse.

## Architecture (ELT)

```
Postgres (raw schema — simulated production source)
  │
  ├─ extract_jobs/postgres_extract  (incremental, based on updated_at)
  │     → MinIO raw/ (Parquet, partitioned by extract_date)
  │
  └─ extract_jobs/macro_extract  (frankfurter.app USD/VND rate)
        → MinIO raw/ (Parquet, partitioned by extract_date)

MinIO raw/ (Data Lake)
  │
  ▼
spark_jobs  (transform: business rules, join application + bureau + fx_rate)
  │
  ▼
Postgres dwh / feature schema (Data Warehouse)
  │
  ▼
serving/  (FastAPI scoring endpoint)
```

Orchestration is handled by Airflow (`airflow/dags/`), scheduling extract jobs and the
Spark transform job. The previous CDC/Kafka/Flink streaming design (Debezium → Kafka → Flink)
was intentionally dropped in favor of this batch ELT pattern; it may be revisited in a
separate project.

## Folder Overview

- `database/` — Postgres schema + table init scripts (raw / dwh / feature), including
  `raw.etl_checkpoint` used for incremental extract bookkeeping
- `backend_simulator/` — simulates Home Credit as a live production system writing to
  `raw.application` / `raw.bureau` in Postgres (INSERT + random UPDATE)
- `extract_jobs/`
  - `postgres_extract/` — incremental extract from Postgres → MinIO Parquet
  - `macro_extract/` — daily FX rate extract from frankfurter.app → MinIO Parquet
  - `utils/` — shared MinIO client + checkpoint helpers
- `spark_jobs/` — Spark jobs reading from MinIO raw layer, applying business DQ + macro
  enrichment, writing into `dwh.*` / `feature.*` in Postgres
- `airflow/` — centralized DAGs orchestrating extract jobs and Spark transform, all running
  inside Docker Compose alongside Postgres/MinIO
- `serving/` — FastAPI scoring endpoint reading from `feature.application_features`
- `data/` — raw Home Credit CSVs and small samples for local dev
- `notebooks/` — EDA and exploratory validation (not used in production jobs)
- `scripts/` — convenience scripts to bring up the stack, seed data, run extract jobs manually

## Getting Started

1. Copy `.env.example` to `.env` and fill in values.
2. Place `application_train.csv` and `bureau.csv` under `data/raw/home_credit/`.
3. `docker compose up -d postgres minio`
4. `docker compose up --build backend_simulator`
5. `bash scripts/run_extract_jobs.sh` (manual test of extract jobs before Airflow takes over)
