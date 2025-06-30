import os
import time
import sys
from dotenv import load_dotenv
from shared.logging_utils import get_logger
from database.engine import init_db, engine
from sqlalchemy.exc import OperationalError

# TODO: use a config_service instead of load_dotenv
# TODO: use a logger here instead of print statements
logger = get_logger('Postgres_Init')
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
MAX_RETRIES = 10
DELAY = 3  # seconds


def wait_for_db():
    # TODO: this function can be repurposed into a general `wait_for`
    #       and added to my python-utilities package
    logger.debug("Waiting for the database to be ready...")
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # engine = create_engine(DATABASE_URL)
            with engine.connect():
                logger.info("Database is initialized and ready!")
                return
        except OperationalError as e:
            logger.warning(
                f"Database not ready yet (attempt {retries + 1}/{MAX_RETRIES}): {str(e)}")
            time.sleep(DELAY)
            retries += 1
    logger.error("Exceeded maximum retry attempts. Exiting")
    sys.exit(1)


if __name__ == "__main__":
    wait_for_db()
    init_db()
