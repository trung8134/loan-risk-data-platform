-- Bảng quản lý checkpoint cho incremental extract (ELT pattern).
-- Mỗi lần extract_jobs/postgres_extract chạy xong, nó cập nhật last_extracted_at
-- của bảng tương ứng trong này. Lần chạy kế tiếp sẽ query:
--   WHERE updated_at > last_extracted_at
-- để chỉ lấy record mới/thay đổi, không phải full table mỗi lần.

CREATE TABLE IF NOT EXISTS raw.etl_checkpoint (
    source_table        VARCHAR(100) PRIMARY KEY,  -- vd: 'raw.application', 'raw.bureau'
    last_extracted_at   TIMESTAMP NOT NULL DEFAULT '1970-01-01',
    last_run_at         TIMESTAMP,
    last_row_count      INT DEFAULT 0
);

-- Seed checkpoint ban đầu cho 2 bảng cần extract — nếu không insert sẵn,
-- lần chạy đầu tiên job phải tự xử lý trường hợp "chưa có checkpoint" (coi như full extract).
INSERT INTO raw.etl_checkpoint (source_table, last_extracted_at)
VALUES
    ('raw.application', '1970-01-01'),
    ('raw.bureau', '1970-01-01')
ON CONFLICT (source_table) DO NOTHING;
