import os
import time
import sys
from dotenv import load_dotenv
from database.engine import init_db, engine
from sqlalchemy.exc import OperationalError

# TODO: use a config_service instead of load_dotenv
# TODO: use a logger here instead of print statements
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
MAX_RETRIES = 10
DELAY = 3  # seconds


def wait_for_db():
    # TODO: this function can be repurposed into a general `wait_for`
    #       and added to my python-utilities package
    print("Waiting for the database to be ready...")
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # engine = create_engine(DATABASE_URL)
            with engine.connect():
                print("\nDatabase is ready!")
                return
        except OperationalError as e:
            print(
                f"Database not ready yet (attempt {retries + 1}/{MAX_RETRIES}): {str(e)}")
            time.sleep(DELAY)
            retries += 1
    print("Exceeded maximum retry attempts. Exiting.")
    sys.exit(1)


if __name__ == "__main__":
    wait_for_db()
    init_db()
    print("Database initialized with tables.")
