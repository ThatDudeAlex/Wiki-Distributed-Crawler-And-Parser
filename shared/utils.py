from datetime import datetime
import hashlib
from urllib.parse import urlparse, urljoin, urlunparse
from zoneinfo import ZoneInfo
from shared.config import EXCLUDED_PREFIXES, WIKI_BASE

# TODO: pull any common utility function into the
# my python-utilities package


def normalize_url(href: str) -> str:
    """
    Normalizes a URL by converting to absolute, and removing fragments/query parameters.
    """
    # Convert relative URL to absolute
    full_url = urljoin(WIKI_BASE, href)

    # Remove fragments (#section) and query params (?foo=bar)
    parsed = urlparse(full_url)
    cleaned = parsed._replace(fragment="", query="")
    return urlunparse(cleaned)


# ===== TODO: This methods seem better suited in the filter rules =====
def is_external_link(href: str) -> bool:
    """
    Determines if a given href points to an external (non-Wikipedia) link
    """

    return not is_internal_link(href)


def is_internal_link(href: str) -> bool:
    """
    Determines if a given href points to an external (non-Wikipedia) link
    """
    parsed = urlparse(href)
    # Check for http/https scheme and ensure it's in a Wikipedia domain
    # 'wikipedia.org'
    return parsed.scheme in ["http", "https"] and \
        "wikipedia.org" in parsed.netloc


# TODO: Move this into Scheduler (is part of filtering)
def has_excluded_prefix(href: str) -> bool:
    """
    Excludes Non-Article Wikipedia Pages
    """
    # strip fragment/query to test path alone
    path = urlparse(href).path

    # check if it's in any excluded namespace
    for prefix in EXCLUDED_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def is_home_page(href: str) -> bool:
    parsed = urlparse(href)
    return parsed.path.strip("/") == "" and parsed.netloc in ["", "en.wikipedia.org"]

# =====================================================================================


def create_hash(content: str) -> str:
    # Create a SHA-256 hash object
    hash_object = hashlib.sha256()

    # Update the hash object with the bytes of the url string
    hash_object.update(content.encode())

    # return the hexadecimal representation of the hash
    return hash_object.hexdigest()


def get_timestamp_eastern_time(isoformat: bool = False) -> datetime | str:
    """Returns an isoformat timestamp in timezone: America/New_York"""
    if isoformat:
        return datetime.now(ZoneInfo("America/New_York")).isoformat()

    return datetime.now(ZoneInfo("America/New_York"))
