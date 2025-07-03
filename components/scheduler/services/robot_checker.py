
import urllib.robotparser

from shared.config import BASE_HEADERS, ROBOTS_TXT


def robot_blocks_crawling(url: str) -> bool:
    """
    Returns True if robots.txt blocks crawling the URL; otherwise, False
    """
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(ROBOTS_TXT)
    rp.read()

    if rp.can_fetch(BASE_HEADERS['user-agent'], url):
        return False
    return True
