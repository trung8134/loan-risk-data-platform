-- Tạo 3 schema chính cho dự án
CREATE SCHEMA IF NOT EXISTS raw;      -- dữ liệu thô từ Home Credit + macro API, chưa xử lý
CREATE SCHEMA IF NOT EXISTS dwh;      -- dữ liệu đã chuẩn hóa, sau Bronze/business DQ
CREATE SCHEMA IF NOT EXISTS feature;  -- bảng feature cuối cho model scoring (Gold)
