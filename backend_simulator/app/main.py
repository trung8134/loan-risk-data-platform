from app.db.connection import get_connection
from app.generators.application_generator import seed_application
from app.generators.bureau_generator import seed_bureau
from app.logging_config import setup_logging

logger = setup_logging("backend_simulator")

def run():
    logger.info("Starting one-time seed of raw.application and raw.bureau...")

    conn = get_connection()
    try:
        app_count = seed_application(conn)
        logger.info("Seed application complete: %s rows inserted.", app_count)

        bureau_count = seed_bureau(conn)
        logger.info("Seed bureau complete: %s rows inserted.", bureau_count)

        logger.info("Seed finished. Container will now exit.")
    finally:
        conn.close()


if __name__ == "__main__":
    run()