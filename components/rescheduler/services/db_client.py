import requests
import os
from urllib.parse import urljoin
from dotenv import load_dotenv


class DBReaderClient:
    """
    Uses a single Session for communication with the db_reader
    This is done to optimize performance by preventing the creation of a new session on every request
    """

    def __init__(self, host: str = None):
        load_dotenv()
        self._base_url = host or os.getenv('DB_READER_HOST')
        if not self._base_url:
            raise ValueError(
                "DB_READER_HOST must be provided either as an argument or environment variable")
        self._session = requests.Session()

    def get_pages_need_rescheduling(self) -> list:
        try:
            db_url = urljoin(self._base_url, '/get_need_rescheduling')
            response = self._session.get(db_url, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(self._base_url)
            print(f"Exception: {e}")
            if e.response:
                print(f"Status code: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
