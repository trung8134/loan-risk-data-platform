-- Bảng chính: mỗi dòng là 1 hồ sơ vay (application) từ Home Credit dataset.
-- Backend simulator INSERT/UPDATE liên tục vào bảng này để giả lập traffic production thật.
-- Extract job (extract_jobs/postgres_extract) đọc incremental dựa trên updated_at,
-- ghi snapshot mới vào MinIO raw layer (Parquet) theo lịch (Airflow).

CREATE TABLE IF NOT EXISTS raw.application (
    sk_id_curr          BIGINT PRIMARY KEY,        -- ID hồ sơ vay (giữ nguyên tên cột gốc Home Credit)
    target              SMALLINT,                  -- 1 = có khó khăn trả nợ, 0 = không (chỉ có ở training data)
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
    days_birth          INT,                       -- số ngày âm tính từ ngày sinh đến ngày nộp hồ sơ
    days_employed       INT,
    application_date    DATE NOT NULL DEFAULT CURRENT_DATE,  -- ngày nộp hồ sơ (dùng để join với macro data)
    created_at          TIMESTAMP NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP NOT NULL DEFAULT now()
);

-- Index hỗ trợ join với macro data theo ngày
CREATE INDEX IF NOT EXISTS idx_application_date ON raw.application (application_date);

-- Index hỗ trợ incremental extract: WHERE updated_at > :last_checkpoint
CREATE INDEX IF NOT EXISTS idx_application_updated_at ON raw.application (updated_at);


-- Bảng phụ: lịch sử tín dụng từ bureau (rút gọn) — phục vụ mở rộng feature sau này
CREATE TABLE IF NOT EXISTS raw.bureau (
    sk_id_bureau        BIGINT PRIMARY KEY,
    sk_id_curr          BIGINT NOT NULL REFERENCES raw.application (sk_id_curr),
    credit_active       VARCHAR(50),
    credit_currency     VARCHAR(20),
    days_credit         INT,
    amt_credit_sum      NUMERIC(14,2),
    amt_credit_sum_debt NUMERIC(14,2),
    created_at          TIMESTAMP NOT NULL DEFAULT now(),
    updated_at          TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_bureau_sk_id_curr ON raw.bureau (sk_id_curr);
CREATE INDEX IF NOT EXISTS idx_bureau_updated_at ON raw.bureau (updated_at);
