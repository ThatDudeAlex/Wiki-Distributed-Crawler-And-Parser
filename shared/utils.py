from datetime import datetime
import hashlib
from typing import Any, Dict
from urllib.parse import urlparse, urljoin, urlunparse
from zoneinfo import ZoneInfo
from shared.config import EXCLUDED_PREFIXES, WIKI_BASE
from jsonschema.exceptions import ValidationError
import jsonschema

# TODO: pull any common utility function into the
# my python-utilities package


def normalize_url(href: str) -> str:
    # Convert relative URL to absolute
    full_url = urljoin(WIKI_BASE, href)

    # Remove fragments (#section) and query params (?foo=bar)
    parsed = urlparse(full_url)
    cleaned = parsed._replace(fragment="", query="")
    return urlunparse(cleaned)


def is_external_link(href: str) -> bool:
    parsed = urlparse(href)
    return parsed.scheme in ["http", "https"] and "wikipedia.org" not in parsed.netloc


def has_excluded_prefix(href: str) -> bool:
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


def create_hash(content: str) -> str:
    # Create a SHA-256 hash object
    hash_object = hashlib.sha256()

    # Update the hash object with the bytes of the url string
    hash_object.update(content.encode())

    # return the hexadecimal representation of the hash
    return hash_object.hexdigest()


def get_timestamp_eastern_time():
    """Returns an isoformat timestamp in timezone: America/New_York"""
    return datetime.now(ZoneInfo("America/New_York")).isoformat()


def validate_param(value, name, expected_type):
    # TODO: use this across various class methods
    if value is None:
        raise ValueError(f"{name} is required")
    if not isinstance(value, expected_type):
        raise TypeError(f"{name} must be of type {expected_type.__name__}")


def validate_message(message: dict, schema: Dict[str, Any]):
    try:
        jsonschema.validate(instance=message, schema=schema)
        # LOGGER.debug("Message is valid.")
    except ValidationError as e:
        # LOGGER.error("Message validation failed: ", e.message)
        raise
