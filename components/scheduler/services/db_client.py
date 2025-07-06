import requests
import os
from urllib.parse import urljoin
from dotenv import load_dotenv

load_dotenv()


class DBReaderClient:
    """
    Uses a single Session for communication with the db_reader
    This is done to optimize performance by preventing the creation of a new session on every request
    """

    def __init__(self, host: str = None):
        self._base_url = host or os.getenv('DB_READER_HOST')
        if not self._base_url:
            raise ValueError(
                "DB_READER_HOST must be provided either as an argument or environment variable")
        self._session = requests.Session()

    def in_db_cache(self, url: str) -> bool:
        try:
            db_url = urljoin(self._base_url, '/url_cache')
            response = self._session.get(
                db_url, params={"url": url}, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            return data.get('is_cached', False)
        except requests.RequestException:
            return False
