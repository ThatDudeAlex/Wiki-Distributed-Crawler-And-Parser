import logging
import urllib.robotparser
from shared.config import ROBOTS_TXT, BASE_HEADERS


class RobotHandler:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._rp = urllib.robotparser.RobotFileParser()
        self._rp.set_url(ROBOTS_TXT)
        self._rp.read()

    def allows_crawling(self, url: str) -> bool:
        """
        Returns ``True`` if robot.txt allows crawling the ``URL`` else
        returns ``False``
        """
        if not self._rp.can_fetch(BASE_HEADERS['user-agent'], url):
            self._logger.warning(f"Blocked by robots.txt: {url}")
            return False
        return True
