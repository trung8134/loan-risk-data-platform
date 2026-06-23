-- Data Warehouse layer (dwh schema) — nơi Spark LOAD dữ liệu sau khi transform
-- từ Parquet trong MinIO raw layer. Đây đóng vai trò "data warehouse" của ELT pattern
-- (ví dụ thực tế tương đương Snowflake/BigQuery, nhưng dùng Postgres cho đơn giản).

CREATE TABLE IF NOT EXISTS dwh.application (
    sk_id_curr          BIGINT PRIMARY KEY,
    target              SMALLINT,
    name_contract_type  VARCHAR(50),
    code_gender         CHAR(1),
    flag_own_car        CHAR(1),
    flag_own_realty     CHAR(1),
    cnt_children        SMALLINT,
    amt_income_total    NUMERIC(14,2),
    amt_credit          NUMERIC(14,2),
    amt_annuity         NUMERIC(14,2),
    amt_goods_price     NUMERIC(14,2),
    name_income_type    VARCHAR(50),
    name_education_type VARCHAR(100),
    name_family_status  VARCHAR(50),
    name_housing_type   VARCHAR(50),
    days_birth          INT,
    days_employed       INT,
    application_date    DATE,
    usd_vnd_rate         NUMERIC(12,4),   -- enrich từ macro data theo application_date
    loaded_at            TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dwh.bureau (
    sk_id_bureau        BIGINT PRIMARY KEY,
    sk_id_curr          BIGINT,
    credit_active       VARCHAR(50),
    credit_currency     VARCHAR(20),
    days_credit         INT,
    amt_credit_sum      NUMERIC(14,2),
    amt_credit_sum_debt NUMERIC(14,2),
    loaded_at            TIMESTAMP NOT NULL DEFAULT now()
);

-- Feature layer — bảng feature cuối cho model scoring (Gold layer trong terminology Medallion)
CREATE TABLE IF NOT EXISTS feature.application_features (
    sk_id_curr              BIGINT PRIMARY KEY,
    target                  SMALLINT,
    income_credit_ratio     NUMERIC(10,4),   -- amt_income_total / amt_credit
    annuity_income_ratio    NUMERIC(10,4),   -- amt_annuity / amt_income_total
    age_years               INT,             -- abs(days_birth) / 365
    employed_years          NUMERIC(10,2),   -- abs(days_employed) / 365
    total_bureau_credit_sum NUMERIC(14,2),   -- tổng amt_credit_sum từ bureau
    usd_vnd_rate              NUMERIC(12,4),
    built_at                  TIMESTAMP NOT NULL DEFAULT now()
);
