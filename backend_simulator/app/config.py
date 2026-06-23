import os


class Settings:
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "loan_credit")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "admin")

    # Đường dẫn file CSV Home Credit (mount read-only vào container)
    APPLICATION_CSV_PATH: str = os.getenv(
        "APPLICATION_CSV_PATH", "/app/data/raw/home_credit/application_train.csv"
    )
    BUREAU_CSV_PATH: str = os.getenv(
        "BUREAU_CSV_PATH", "/app/data/raw/home_credit/bureau.csv"
    )


settings = Settings()
