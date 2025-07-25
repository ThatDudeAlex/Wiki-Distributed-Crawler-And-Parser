import logging
from typing import Optional
import requests
import os
from urllib.parse import urljoin
from dotenv import load_dotenv

load_dotenv()

class DBReaderClient:
    """
    HTTP client for communicating with the db_reader microservice

    Uses a persistent requests.Session for performance
    """


    def __init__(self, logger: logging.Logger, db_timeout: int, host: str = None) -> None:
        """
        Initialize the DBReaderClient

        Args:
            host (str, optional): Base URL for db_reader. If not provided,
                                  uses the DB_READER_HOST environment variable.

        Raises:
            ValueError: If no host is provided or found in environment
        """
        self._logger = logger
        self.db_timeout = db_timeout
        self._base_url = host or os.getenv('DB_READER_HOST')
        
        if not self._base_url:
            raise ValueError(
                "DB_READER_HOST must be provided either as an argument or environment variable")
        
        self._session = requests.Session()


    def pop_links_from_schedule(self, count: int) -> Optional[list]:
        """
        Request a number of scheduled links from the db_reader service

        Args:
            count (int): Number of links to retrieve

        Returns:
            Optional[list]: List of links or None on failure
        """

        try:
            db_url = urljoin(self._base_url, '/get_scheduled_links')
            response = self._session.get(db_url, params={"count": count}, timeout=self.db_timeout)
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException:
            self._logger.exception("Failed to fetch scheduled links from db_reader")


    def tables_are_empty(self) -> Optional[bool]:
        """
        Check whether relevant database tables are empty

        Returns:
            Optional[bool]: True if empty, False if not, or None on failure
        """

        try:
            db_url = urljoin(self._base_url, '/tables/empty')
            response = self._session.get(db_url, timeout=self.db_timeout)
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException:
            self._logger.exception("Failed to check if db_reader tables are empty")
