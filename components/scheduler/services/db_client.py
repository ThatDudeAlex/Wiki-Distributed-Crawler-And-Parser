import requests
import os
from urllib.parse import urljoin
from dotenv import load_dotenv


class DBReaderClient:
    """
    Uses a single Session for communication between with the db_reader. This
    is done in order to optimize performance by prevening the creation a new
    session on every request
    """

    def __init__(self, host: str):
        load_dotenv()
        self._base_url = host if host else os.getenv('DB_READER_HOST')
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
