import psycopg2
from psycopg2.extensions import connection as PgConnection

from app.config import settings


def get_connection() -> PgConnection:
    return psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
    )
