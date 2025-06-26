import logging
import requests
from ratelimit import limits, sleep_and_retry


class Fetcher:
    def __init__(self, logger: logging.Logger, headers: dict = None):
        self._logger = logger
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)

    @sleep_and_retry
    @limits(calls=1, period=1)  # 1 request per second
    def get(self, url, **kwargs):
        r"""Sends a GET request.

        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """
        try:
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            logging.error(
                f"HTTP error occurred: {e} - Status Code: {response.status_code}")
            raise  # Re-raise the same http error exception
